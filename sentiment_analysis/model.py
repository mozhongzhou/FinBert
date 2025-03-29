import torch
from torch import nn
from transformers import AutoModel, AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from typing import List, Dict, Tuple, Union

class FinBertSentimentAnalyzer:
    """使用FinBERT模型进行金融文本情感分析"""
    
    def __init__(self, model_name: str = "ProsusAI/finbert", device: str = None):
        """
        初始化FinBERT情感分析器
        
        Args:
            model_name: 预训练模型名称，默认为'ProsusAI/finbert'
            device: 运行设备，None则自动选择
        """
        self.model_name = model_name
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        
        print(f"加载模型 {model_name} 到 {self.device} 设备...")
        
        # 加载模型和分词器
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        
        # FinBERT标签映射
        self.id2label = {
            0: "negative",  # 负面/利空
            1: "neutral",   # 中性
            2: "positive"   # 正面/利好
        }
        
        self.label2id = {v: k for k, v in self.id2label.items()}
        
        print("模型加载完成")
    
    def analyze_text(self, text: str) -> Dict:
        """
        分析单个文本的情感
        
        Args:
            text: 要分析的文本
            
        Returns:
            包含情感标签和置信度的字典
        """
        # 处理过长的文本
        max_length = self.tokenizer.model_max_length
        if len(text.split()) > max_length - 10:  # 保留一些余量
            print(f"警告: 文本过长，将被截断至 {max_length} 个token")
        
        # 分词和推理
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probabilities = torch.nn.functional.softmax(logits, dim=1).squeeze().cpu().numpy()
        
        # 找出最高概率的类别
        predicted_class_id = np.argmax(probabilities)
        predicted_label = self.id2label[predicted_class_id]
        
        # 构建结果字典
        result = {
            "label": predicted_label,
            "confidence": {
                "negative": float(probabilities[0]),
                "neutral": float(probabilities[1]),
                "positive": float(probabilities[2])
            },
            "text": text
        }
        
        return result
    
    def analyze_batch(self, texts: List[str], batch_size: int = 8) -> List[Dict]:
        """
        批量分析多个文本的情感
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
            
        Returns:
            情感分析结果列表
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # 分词
            inputs = self.tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True).to(self.device)
            
            # 推理
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=1).cpu().numpy()
            
            # 处理每个文本的结果
            for j, probs in enumerate(probabilities):
                predicted_class_id = np.argmax(probs)
                predicted_label = self.id2label[predicted_class_id]
                
                result = {
                    "label": predicted_label,
                    "confidence": {
                        "negative": float(probs[0]),
                        "neutral": float(probs[1]),
                        "positive": float(probs[2])
                    },
                    "text": batch_texts[j]
                }
                results.append(result)
        
        return results
    
    def analyze_sentences(self, sentences: List[str]) -> List[Dict]:
        """分析句子列表"""
        return self.analyze_batch(sentences)
    
    def analyze_document(self, document: str, split_sentences: bool = True) -> Dict:
        """
        分析整个文档，可选择是否分句分析
        
        Args:
            document: 文档文本
            split_sentences: 是否分句分析
            
        Returns:
            文档级别和句子级别的情感分析结果
        """
        import nltk
        
        # 确保已下载分句模型
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        # 分句分析
        if split_sentences:
            sentences = nltk.sent_tokenize(document)
            # 过滤掉过短的句子
            valid_sentences = [sent for sent in sentences if len(sent.split()) > 5]
            
            sentence_results = self.analyze_batch(valid_sentences)
        else:
            sentence_results = []
        
        # 整体文档分析
        document_result = self.analyze_text(document)
        
        return {
            "document": document_result,
            "sentences": sentence_results
        }

# 扩展模型 - 使用自定义的金融领域微调模型
class CustomFinancialSentimentAnalyzer(FinBertSentimentAnalyzer):
    """使用自定义微调的金融情感分析模型"""
    
    def __init__(self, model_path: str, device: str = None):
        """
        初始化自定义金融情感分析器
        
        Args:
            model_path: 微调模型的路径
            device: 运行设备
        """
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        
        print(f"从 {model_path} 加载自定义模型...")
        
        # 加载本地保存的模型和分词器
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.to(self.device)
        
        # 使用模型的标签映射或定义自己的
        if hasattr(self.model.config, 'id2label'):
            self.id2label = self.model.config.id2label
        else:
            self.id2label = {
                0: "negative",
                1: "neutral",
                2: "positive"
            }
        
        self.label2id = {v: k for k, v in self.id2label.items()}
        
        print("自定义模型加载完成") 