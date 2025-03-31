import os
import json
import openai
import time
from typing import Dict, List, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/gpt_explainer.log"),
        logging.StreamHandler()
    ]
)

class GPTFinancialExplainer:
    """使用GPT模型为金融文本提供解释性分析"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        初始化GPT金融解释器
        
        Args:
            api_key: OpenAI API密钥，如果为None则尝试从环境变量获取
            model: 要使用的GPT模型名称
        """
        # 设置API密钥
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("需要提供OpenAI API密钥，请通过参数或设置OPENAI_API_KEY环境变量")
        
        openai.api_key = self.api_key
        self.model = model
        logging.info(f"GPT金融解释器初始化成功，使用模型: {model}")
    
    def explain_sentiment(self, text: str, sentiment_label: str, confidence: Dict[str, float]) -> Dict[str, str]:
        """
        解释金融文本的情感分析结果
        
        Args:
            text: 要分析的金融文本
            sentiment_label: FinBERT给出的情感标签 (positive/neutral/negative)
            confidence: FinBERT给出的置信度字典
            
        Returns:
            包含解释的字典
        """
        # 构建提示
        confidence_str = ", ".join([f"{k}: {v:.2f}" for k, v in confidence.items()])
        
        prompt = f"""作为金融分析专家，分析这段10-K年报文本:
        "{text}"
        
        FinBERT情感分析结果: {sentiment_label} (置信度: {confidence_str})
        
        请简要分析这段文本对投资者的含义。考虑:
        1. 这段内容传达了哪些关键信息？
        2. 为什么它会被判断为{sentiment_label}？
        3. 对投资者决策有何影响？
        
        保持回答简洁，不超过3-5句话。"""
        
        # 调用GPT API
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "你是一位金融分析专家，对10-K报告文本进行简洁、专业的解读。"},
                         {"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.5
            )
            explanation = response.choices[0].message.content.strip()
            
            return {
                "explanation": explanation,
                "model": self.model
            }
            
        except Exception as e:
            logging.error(f"调用GPT API时出错: {str(e)}")
            return {
                "explanation": f"无法提供解释: {str(e)}",
                "model": self.model,
                "error": str(e)
            }
    
    def explain_batch(self, sentences_with_sentiment: List[Dict]) -> List[Dict]:
        """
        批量解释多个句子的情感分析结果
        
        Args:
            sentences_with_sentiment: 包含文本和情感分析结果的字典列表
            
        Returns:
            添加了解释的句子列表
        """
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
            
            # 对重要的情感文本调用API解释
            if label in ['positive', 'negative'] and max(confidence.values()) > 0.7:
                explanation = self.explain_sentiment(text, label, confidence)
                item['explanation'] = explanation.get('explanation', '无法提供解释')
                
                # 加入延迟避免API限制
                time.sleep(0.5)
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
    
    def explain_report_section(self, section_data: Dict) -> Dict:
        """
        解释报告的一个章节
        
        Args:
            section_data: 章节数据，包含句子及其情感分析
            
        Returns:
            添加了章节整体解释的章节数据
        """
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
        
        请保持分析简洁精炼，150字以内。"""
        
        # 调用GPT API
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "你是一位资深金融分析师，专注于分析10-K报告章节的整体意义和对投资者的价值。"},
                         {"role": "user", "content": summary_text}],
                max_tokens=250,
                temperature=0.5
            )
            section_explanation = response.choices[0].message.content.strip()
            
            # 更新章节数据
            section_data['section_explanation'] = section_explanation
            
        except Exception as e:
            logging.error(f"生成章节解释时出错: {str(e)}")
            section_data['section_explanation'] = "暂时无法提供章节总体分析。"
        
        return section_data


def enrich_results_with_explanations(results: Dict, explainer: GPTFinancialExplainer, include_all: bool = False) -> Dict:
    """
    为情感分析结果添加GPT解释
    
    Args:
        results: FinBERT情感分析的结果字典
        explainer: GPT解释器实例
        include_all: 是否为所有句子添加解释（如果为False，则只为重要句子添加）
        
    Returns:
        添加了解释的结果字典
    """
    enriched_results = {}
    
    for report_key, report_data in results.items():
        enriched_report = {
            'summary': report_data['summary'],
            'sections': {}
        }
        
        for section_name, section_data in report_data['sections'].items():
            # 对重要句子添加解释
            if include_all:
                # 为所有句子添加解释
                enriched_sentences = explainer.explain_batch(section_data['sentences'])
            else:
                # 仅为重要句子添加解释（最显著的正面和负面句子）
                important_sentences = []
                other_sentences = []
                
                for sentence in section_data['sentences']:
                    label = sentence.get('label', '')
                    confidence = sentence.get('confidence', {})
                    max_conf = max(confidence.values()) if confidence else 0
                    
                    if (label in ['positive', 'negative']) and max_conf > 0.8:
                        important_sentences.append(sentence)
                    else:
                        other_sentences.append(sentence)
                
                # 为重要句子添加GPT解释，为其他句子添加简单解释
                explained_important = explainer.explain_batch(important_sentences)
                
                # 对其他句子添加简单解释
                for sentence in other_sentences:
                    label = sentence.get('label', '')
                    if label == 'positive':
                        sentence['explanation'] = "积极信息，可能有利于公司发展。"
                    elif label == 'negative':
                        sentence['explanation'] = "消极信息，可能存在风险或挑战。"
                    else:
                        sentence['explanation'] = "中性描述，主要陈述事实。"
                
                # 合并结果
                enriched_sentences = explained_important + other_sentences
            
            # 更新章节数据
            updated_section = section_data.copy()
            updated_section['sentences'] = enriched_sentences
            
            # 为章节添加整体解释
            updated_section = explainer.explain_report_section(updated_section)
            
            enriched_report['sections'][section_name] = updated_section
        
        enriched_results[report_key] = enriched_report
    
    return enriched_results


if __name__ == "__main__":
    import argparse
    from sentiment_analysis.model import FinBertSentimentAnalyzer
    from sentiment_analysis.predict import analyze_reports
    try:
        from sentiment_analysis.local_llm import LocalLLMExplainer
        local_llm_available = True
    except ImportError:
        local_llm_available = False
        print("警告: 本地LLM模型依赖未安装，无法使用本地模型。请安装 transformers, torch, accelerate, bitsandbytes 等依赖。")
    
    parser = argparse.ArgumentParser(description="分析10-K报告并添加解释")
    parser.add_argument("--ticker", type=str, help="股票代码筛选", default=None)
    parser.add_argument("--model", type=str, help="FinBERT模型名称", default="ProsusAI/finbert")
    parser.add_argument("--explainer", type=str, choices=["gpt", "local"], help="解释器类型", default="local")
    parser.add_argument("--gpt_model", type=str, help="GPT模型名称", default="gpt-3.5-turbo")
    parser.add_argument("--local_model", type=str, help="本地LLM模型名称", default="Qwen/Qwen-7B-Chat") 
    parser.add_argument("--use_4bit", action="store_true", help="是否使用4bit量化以节省显存", default=True)
    parser.add_argument("--api_key", type=str, help="OpenAI API密钥", default=None)
    parser.add_argument("--all", action="store_true", help="为所有句子添加解释")
    
    args = parser.parse_args()
    
    # 初始化FinBERT分析器
    analyzer = FinBertSentimentAnalyzer(model_name=args.model)
    
    # 使用FinBERT分析报告
    results = analyze_reports(analyzer, ticker=args.ticker)
    
    # 选择解释器类型
    if args.explainer == "gpt":
        explainer = GPTFinancialExplainer(api_key=args.api_key, model=args.gpt_model)
        print(f"使用OpenAI GPT模型 {args.gpt_model} 进行解释")
    else:
        if not local_llm_available:
            print("本地LLM模型不可用，回退到GPT模型")
            explainer = GPTFinancialExplainer(api_key=args.api_key, model=args.gpt_model)
        else:
            try:
                explainer = LocalLLMExplainer(model_name=args.local_model, use_4bit=args.use_4bit)
                print(f"使用本地模型 {args.local_model} 进行解释")
            except Exception as e:
                print(f"加载本地模型失败: {e}，回退到GPT模型")
                explainer = GPTFinancialExplainer(api_key=args.api_key, model=args.gpt_model)
    
    # 添加解释
    enriched_results = enrich_results_with_explanations(results, explainer, include_all=args.all)
    
    # 保存结果
    output_file = os.path.join("results", f"{'all' if not args.ticker else args.ticker}_with_explanations.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enriched_results, f, ensure_ascii=False, indent=2)
    
    print(f"分析和解释完成，结果已保存到 {output_file}") 