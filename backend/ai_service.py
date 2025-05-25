import os
import json
import httpx
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# 配置DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-48d545318caf466ba6fa14637c047169")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 2000
    stream: bool = False

class ChatResponse(BaseModel):
    response: str
    usage: Optional[Dict[str, Any]] = None

async def generate_ai_response(request: ChatRequest) -> ChatResponse:
    """
    调用DeepSeek API生成回复
    """
    if not DEEPSEEK_API_KEY:
        # 如果没有API密钥，返回一个模拟响应
        return ChatResponse(
            response="我是一个模拟的AI助手。由于没有配置DeepSeek API密钥，我无法提供真实的AI回复。请联系管理员配置API密钥。",
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        )
    
    # 法律咨询系统提示
    legal_system_prompt = {
        "role": "system",
        "content": """你是一名持有中国执业资格的律师，专注于综合法律领域，包括劳动法、合同法、婚姻法和民商事纠纷等。请以通俗易懂的方式解答问题，并明确说明回答的法律依据（如《中华人民共和国民法典》第X条）。

免责声明：
你的回答不构成正式法律意见，具体案件请建议用户咨询线下律师。当前信息基于中国大陆法律，如涉及其他地区请说明。

回答格式：
1. 先简要分析用户的法律问题
2. 提供相关法律条文和依据
3. 给出具体的法律建议和可操作性方案
4. 如有必要，说明潜在风险和注意事项

请保持专业、客观，同时语言应平易近人，避免过多专业术语。"""
    }
    
    # 准备发送给DeepSeek API的请求数据
    messages = [legal_system_prompt]
    messages.extend([{"role": msg.role, "content": msg.content} for msg in request.messages])
    
    payload = {
        "model": request.model,
        "messages": messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "stream": request.stream
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                DEEPSEEK_API_URL,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                # 处理API错误
                error_detail = response.json().get("error", {}).get("message", "Unknown error")
                return ChatResponse(
                    response=f"API请求错误: {error_detail}",
                    usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                )
            
            # 解析API响应
            result = response.json()
            assistant_message = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = result.get("usage", {})
            
            return ChatResponse(
                response=assistant_message,
                usage=usage
            )
            
    except Exception as e:
        # 处理网络或其他错误
        return ChatResponse(
            response=f"发生错误: {str(e)}",
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        )

# 模拟AI响应的函数，用于测试或当API密钥未配置时
def generate_mock_response(messages: List[ChatMessage]) -> str:
    """
    生成模拟的AI回复，用于测试
    """
    last_message = messages[-1].content if messages else ""
    
    # 简单的法律问题回复模板
    if "合同" in last_message:
        return "关于合同问题，您需要注意以下几点：\n\n1. 合同的有效性取决于双方是否具有完全民事行为能力\n2. 合同条款应当明确，不存在歧义\n3. 合同内容不得违反法律法规的强制性规定\n\n建议您在签订合同前咨询专业律师，确保您的权益得到保障。"
    
    elif "侵权" in last_message:
        return "侵权行为需要满足四个构成要件：\n\n1. 行为人实施了加害行为\n2. 受害人的合法权益受到损害\n3. 加害行为与损害后果之间存在因果关系\n4. 行为人主观上有过错\n\n如果您认为自己的权益受到侵害，建议收集相关证据并寻求法律援助。"
    
    elif "劳动" in last_message or "工作" in last_message:
        return "根据《中华人民共和国劳动法》，劳动者享有以下权利：\n\n1. 平等就业和选择职业的权利\n2. 取得劳动报酬的权利\n3. 休息休假的权利\n4. 获得劳动安全卫生保护的权利\n5. 接受职业技能培训的权利\n6. 享受社会保险和福利的权利\n7. 提请劳动争议处理的权利\n\n如果您的劳动权益受到侵害，可以向劳动监察部门投诉或申请劳动仲裁。"
    
    elif "婚姻" in last_message or "离婚" in last_message:
        return "关于婚姻家庭问题，《中华人民共和国民法典》婚姻家庭编规定：\n\n1. 结婚应当男女双方完全自愿，不得有任何一方或第三方强迫\n2. 夫妻在婚姻关系存续期间所得的财产，为夫妻共同财产，归夫妻共同所有\n3. 离婚分为协议离婚和诉讼离婚两种方式\n4. 子女抚养、财产分割、债务处理是离婚需要解决的主要问题\n\n建议您针对具体情况咨询专业律师。"
    
    else:
        return "您好，我是您的法律AI助手。我可以回答关于合同、侵权、劳动法、婚姻家庭等方面的法律问题。请详细描述您的问题，我会尽力提供专业的法律建议。请注意，我的回答仅供参考，复杂法律问题建议咨询专业律师。"
