import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", "local_llm.log")) if os.path.exists("logs") else logging.StreamHandler(),
        logging.StreamHandler()
    ]
)

class LocalLLMExplainer:
    """使用本地部署的LLM模型替代GPT进行解释"""
    
    def __init__(self, model_name="Qwen/Qwen-7B-Chat", use_4bit=True, device=None):
        """
        初始化本地LLM解释器
        
        Args:
            model_name: Hugging Face模型名称
            use_4bit: 是否使用4bit量化加载模型节省内存
            device: 运行设备，None则自动选择
        """
        self.model_name = model_name
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        
        logging.info(f"正在加载本地LLM模型: {model_name} 到 {self.device}")
        
        # 配置量化参数
        if use_4bit and self.device == 'cuda':
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True
            )
        else:
            quantization_config = None
        
        # 加载分词器和模型
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        
        # 设置模型加载参数
        model_kwargs = {
            "device_map": "auto",
            "trust_remote_code": True,
        }
        
        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, 
            **model_kwargs
        )
        
        # 根据模型类型处理特殊token和生成设置
        if 'qwen' in model_name.lower():
            self.chat_format = 'qwen'
        elif 'llama' in model_name.lower():
            self.chat_format = 'llama'
        elif 'mistral' in model_name.lower():
            self.chat_format = 'mistral'
        elif 'bloomz' in model_name.lower():
            self.chat_format = 'bloomz'
        else:
            self.chat_format = 'general'  # 通用格式
            
        logging.info(f"本地LLM模型加载完成，使用对话格式: {self.chat_format}")
    
    def _format_prompt(self, prompt):
        """根据不同模型格式化提示"""
        if self.chat_format == 'qwen':
            # 通义千问对话格式
            formatted_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
            return formatted_prompt
        elif self.chat_format == 'llama':
            # Llama 2对话格式
            formatted_prompt = f"<s>[INST] {prompt} [/INST]"
            return formatted_prompt
        elif self.chat_format == 'mistral':
            # Mistral对话格式
            formatted_prompt = f"<s>[INST] {prompt} [/INST]"
            return formatted_prompt
        elif self.chat_format == 'bloomz':
            # BLOOMZ对话格式，简单格式
            return prompt
        else:
            # 通用格式
            return prompt
    
    def _extract_response(self, full_response, prompt):
        """从完整回复中提取模型生成的部分"""
        if self.chat_format == 'qwen':
            # 通义千问格式
            if "<|im_start|>assistant\n" in full_response:
                response = full_response.split("<|im_start|>assistant\n", 1)[1]
                if "<|im_end|>" in response:
                    response = response.split("<|im_end|>")[0]
                return response.strip()
        elif self.chat_format in ['llama', 'mistral']:
            # Llama/Mistral格式
            if "[/INST]" in full_response:
                response = full_response.split("[/INST]", 1)[1]
                return response.strip()
        
        # 默认处理：移除原始提示
        if prompt in full_response:
            return full_response[len(prompt):].strip()
        
        return full_response.strip()
    
    def generate_response(self, prompt, max_new_tokens=512, temperature=0.7):
        """生成回答"""
        formatted_prompt = self._format_prompt(prompt)
        inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.device)
        
        # 生成回答
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1
            )
        
        # 解码并返回生成的文本
        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 提取回答部分(去除输入的prompt)
        response = self._extract_response(full_response, prompt)
        
        return response
    
    def explain_sentiment(self, text, sentiment_label, confidence):
        """解释金融文本的情感分析结果"""
        # 构建适合该模型的提示
        confidence_str = ", ".join([f"{k}: {v:.2f}" for k, v in confidence.items()])
        
        prompt = f"""你是金融分析专家，请简明分析这段10-K年报文本:
        "{text}"
        
        FinBERT情感分析结果: {sentiment_label} (置信度: {confidence_str})
        
        请简要分析这段文本对投资者的含义:
        1. 传达了哪些关键信息？
        2. 为什么它被判断为{sentiment_label}？
        3. 对投资决策有何影响？
        
        请用中文回答，简洁不超过3-5句话。
        """
        
        try:
            explanation = self.generate_response(prompt)
            return {
                "explanation": explanation,
                "model": self.model_name
            }
        except Exception as e:
            logging.error(f"生成解释时出错: {str(e)}")
            return {
                "explanation": f"无法提供解释: {str(e)}",
                "model": self.model_name,
                "error": str(e)
            }
    
    def explain_batch(self, sentences_with_sentiment):
        """批量解释多个句子的情感分析结果"""
        results = []
        
        for item in sentences_with_sentiment:
            text = item.get('text', '')
            label = item.get('label', '')
            confidence = item.get('confidence', {})
            
            # 跳过空文本或中性文本
            if not text or label == 'neutral':
                item['explanation'] = "这是一段中性描述，仅陈述事实，没有明显的积极或消极含义。"
                results.append(item)
                continue
            
            # 对重要的情感文本调用生成解释
            if label in ['positive', 'negative'] and max(confidence.values()) > 0.7:
                explanation = self.explain_sentiment(text, label, confidence)
                item['explanation'] = explanation.get('explanation', '无法提供解释')
            else:
                # 对不那么重要的文本给出简单解释
                if label == 'positive':
                    item['explanation'] = "这段内容传达了积极信息，可能对公司未来发展有利。"
                elif label == 'negative':
                    item['explanation'] = "这段内容传达了消极信息，可能存在风险或挑战。"
                else:
                    item['explanation'] = "这段内容信息价值中等。"
            
            results.append(item)
            
        return results
    
    def explain_report_section(self, section_data):
        """解释报告的一个章节"""
        # 提取章节的关键统计数据
        stats = section_data.get('stats', {})
        proportions = section_data.get('proportions', {})
        
        # 找出最显著的正面和负面句子
        sentences = section_data.get('sentences', [])
        pos_sentences = [s for s in sentences if s.get('label') == 'positive']
        neg_sentences = [s for s in sentences if s.get('label') == 'negative']
        
        # 按置信度排序
        pos_sentences.sort(key=lambda x: x.get('confidence', {}).get('positive', 0), reverse=True)
        neg_sentences.sort(key=lambda x: x.get('confidence', {}).get('negative', 0), reverse=True)
        
        # 获取top句子
        top_pos = pos_sentences[:3] if pos_sentences else []
        top_neg = neg_sentences[:3] if neg_sentences else []
        
        # 构建章节摘要提示
        summary_text = f"""这是一个10-K报告章节的情感分析摘要:
        
        统计数据:
        - 积极句子: {stats.get('positive', 0)} ({proportions.get('positive', 0):.2%})
        - 中性句子: {stats.get('neutral', 0)} ({proportions.get('neutral', 0):.2%})
        - 消极句子: {stats.get('negative', 0)} ({proportions.get('negative', 0):.2%})
        
        最显著的积极内容:
        {' '.join([s.get('text', '')[:150] + '...' for s in top_pos[:1]])}
        
        最显著的消极内容:
        {' '.join([s.get('text', '')[:150] + '...' for s in top_neg[:1]])}
        
        请提供这个章节的总体分析，重点关注:
        1. 这个章节的总体情感倾向是什么？
        2. 哪些关键信息最值得投资者关注？
        3. 与其他类似公司相比，这些内容有何特别之处？
        
        请用中文回答，简洁精炼，150字以内。"""
        
        # 调用本地模型
        try:
            section_explanation = self.generate_response(summary_text, max_new_tokens=250)
            
            # 更新章节数据
            section_data['section_explanation'] = section_explanation
            
        except Exception as e:
            logging.error(f"生成章节解释时出错: {str(e)}")
            section_data['section_explanation'] = "暂时无法提供章节总体分析。"
        
        return section_data


# 测试代码
if __name__ == "__main__":
    # 简单测试示例
    try:
        explainer = LocalLLMExplainer(model_name="Qwen/Qwen-1_8B-Chat", use_4bit=True)
        
        test_text = "公司第四季度的收入增长超过了分析师预期，达到了12.5亿美元，同比增长15%。"
        result = explainer.explain_sentiment(
            test_text, 
            "positive", 
            {"positive": 0.85, "neutral": 0.1, "negative": 0.05}
        )
        
        print("测试文本:", test_text)
        print("解释结果:", result["explanation"])
        
    except Exception as e:
        print(f"测试时出错: {e}") 