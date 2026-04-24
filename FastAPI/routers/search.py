"""
搜索相关路由
"""
from fastapi import APIRouter
import httpx

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/news")
async def search_news(query: str = ""):
    """搜索实时新闻"""
    try:
        # 使用 Bing 搜索 API 获取实时新闻
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 方案1：使用 Bing 搜索（需要 API Key）
            # subscription_key = "your-bing-api-key"
            # response = await client.get(
            #     "https://api.bing.microsoft.com/v7.0/news/search",
            #     headers={"Ocp-Apim-Subscription-Key": subscription_key},
            #     params={"q": query or "最新新闻", "count": 5, "mkt": "zh-CN"}
            # )
            
            # 方案2：使用免费的 RSS 转 JSON 服务（无需 Key）
            # 这里使用公开的新闻聚合接口
            if query:
                search_url = f"https://api.aa1.cn/doc/cctv.html"
            else:
                # 获取CCTV最新国内新闻
                search_url = "https://api.istero.com/resource/v1/cctv/china/latest/news"
            
            response = await client.get(search_url)
            
            if response.status_code == 200:
                data = response.json()
                # 提取新闻标题和摘要
                news_items = []
                if isinstance(data, dict) and 'data' in data:
                    items = data['data'] if isinstance(data['data'], list) else [data['data']]
                    for item in items[:5]:
                        news_items.append({
                            "title": item.get("title", ""),
                            "summary": item.get("description", "")[:100] if item.get("description") else "",
                            "url": item.get("url", "")
                        })
                
                return {
                    "code": 200,
                    "message": "搜索成功",
                    "data": {"news": news_items}
                }
            else:
                return {
                    "code": 500,
                    "message": "搜索服务暂时不可用",
                    "data": {"news": []}
                }
    except Exception as e:
        print(f"搜索新闻失败: {e}")
        return {
            "code": 500,
            "message": f"搜索失败: {str(e)}",
            "data": {"news": []}
        }
