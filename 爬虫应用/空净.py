import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# ====================== Windows 路径配置 ======================
INPUT_EXCEL = r"C:\Users\FOH\Desktop\爬虫.xlsx"
OUTPUT_EXCEL = r"C:\Users\FOH\Desktop\天猫CADR值爬取结果.xlsx"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://tmall.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}
# ===========================================================

def get_tmall_cadr(url):
    try:
        session = requests.Session()
        resp = session.get(url, headers=HEADERS, timeout=25)
        resp.encoding = resp.apparent_encoding
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # 提取整个参数区域（适配你截图里的“参数信息”模块）
        param_area = soup.find("div", class_="attributes-list") or soup.find("div", class_="params-list") or soup.find("div", id="J_AttrUL")
        if param_area:
            text = param_area.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)

        # 针对你截图格式的精准正则
        # 匹配：甲醛CADR值 597立方米/小时
        jq_match = re.search(
            r"甲醛\s*CADR\s*值?\s*(\d+)\s*立方米/小时",
            text,
            re.IGNORECASE
        )
        # 匹配：颗粒物CADR值 747立方米/小时（也兼容截断写法“颗粒物CAD…”）
        klp_match = re.search(
            r"(颗粒物\s*CADR?\s*值?|颗粒物\s*CAD…)\s*(\d+)\s*立方米/小时",
            text,
            re.IGNORECASE
        )

        jq_val = jq_match.group(1) if jq_match else None
        klp_val = klp_match.group(2) if klp_match else None

        return jq_val, klp_val

    except Exception as e:
        print(f"❌ 错误：{str(e)[:40]} | {url[:50]}...")
        return None, None

def main():
    try:
        df = pd.read_excel(INPUT_EXCEL)
        print(f"✅ 读取 {len(df)} 条记录")
    except Exception as e:
        print(f"❌ 读文件失败：{e}")
        return

    brands = df.iloc[:, 0].fillna("未知")
    urls = df.iloc[:, 1].fillna("")

    results = []
    for i, (brand, url) in enumerate(zip(brands, urls), 1):
        if not url.startswith("http"):
            results.append({"品牌名称": brand, "商品链接": url, "甲醛CADR值": "无效链接", "颗粒物CADR值": "无效链接"})
            continue

        print(f"\n[{i}/{len(df)}] 爬取：{brand}")
        jq, klp = get_tmall_cadr(url)
        results.append({
            "品牌名称": brand,
            "商品链接": url,
            "甲醛CADR值": jq if jq else "未找到",
            "颗粒物CADR值": klp if klp else "未找到"
        })
        time.sleep(2)

    result_df = pd.DataFrame(results)
    result_df.to_excel(OUTPUT_EXCEL, index=False, engine="openpyxl")
    print(f"\n🎉 完成！结果在：{OUTPUT_EXCEL}")

if __name__ == "__main__":
    main()