"""
API测试脚本 - 用于测试后端接口是否正常
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from httpx import AsyncClient, ASGITransport
from main import app


async def test_api():
    """测试API接口"""
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        print("=" * 60)
        print("开始测试API接口")
        print("=" * 60)
        
        # 1. 测试根路径
        print("\n1. 测试根路径...")
        response = await client.get("/")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        # 2. 测试获取新闻分类
        print("\n2. 测试获取新闻分类...")
        response = await client.get("/api/news/categories")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   分类数量: {len(data.get('data', []))}")
        
        # 3. 测试用户注册
        print("\n3. 测试用户注册...")
        register_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = await client.post("/api/user/register", json=register_data)
        print(f"   状态码: {response.status_code}")
        reg_result = response.json()
        print(f"   响应: {reg_result.get('message')}")
        
        token = None
        if reg_result.get('code') == 200:
            token = reg_result['data']['token']
            print(f"   Token: {token[:20]}...")
        
        # 4. 测试用户登录
        print("\n4. 测试用户登录...")
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = await client.post("/api/user/login", json=login_data)
        print(f"   状态码: {response.status_code}")
        login_result = response.json()
        print(f"   响应: {login_result.get('message')}")
        
        if login_result.get('code') == 200:
            token = login_result['data']['token']
        
        # 5. 测试获取用户信息（需要Token）
        if token:
            print("\n5. 测试获取用户信息...")
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/api/user/info", headers=headers)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                user_info = response.json()['data']
                print(f"   用户名: {user_info.get('username')}")
        
        # 6. 测试更新个人简介
        if token:
            print("\n6. 测试更新个人简介...")
            headers = {"Authorization": f"Bearer {token}"}
            bio_data = {"bio": "这是我的新简介"}
            response = await client.put("/api/user/update", headers=headers, json=bio_data)
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json().get('message')}")
        
        # 7. 测试收藏功能
        if token:
            print("\n7. 测试添加收藏...")
            headers = {"Authorization": f"Bearer {token}"}
            fav_data = {"newsId": 1}
            response = await client.post("/api/favorite/add", headers=headers, json=fav_data)
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json().get('message')}")
            
            print("\n8. 测试检查收藏状态...")
            response = await client.get("/api/favorite/check?newsId=1", headers=headers)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                is_fav = response.json()['data']['isFavorite']
                print(f"   是否已收藏: {is_fav}")
            
            print("\n9. 测试获取收藏列表...")
            response = await client.get("/api/favorite/list?page=1&pageSize=10", headers=headers)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                fav_list = response.json()['data']
                print(f"   收藏数量: {fav_list.get('total', 0)}")
        
        # 8. 测试浏览历史
        if token:
            print("\n10. 测试添加浏览历史...")
            headers = {"Authorization": f"Bearer {token}"}
            hist_data = {"newsId": 1}
            response = await client.post("/api/history/add", headers=headers, json=hist_data)
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json().get('message')}")
            
            print("\n11. 测试获取浏览历史...")
            response = await client.get("/api/history/list", headers=headers)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                hist_list = response.json()['data']
                print(f"   历史记录数量: {hist_list.get('total', 0)}")
        
        print("\n" + "=" * 60)
        print("API测试完成！")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_api())
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
