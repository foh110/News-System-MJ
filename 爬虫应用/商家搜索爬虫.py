import requests
import csv
import time
import random
import math


class MultiKeywordSpider(object):
    def __init__(self, keywords, region, ak, target_count_per_keyword):
        """
        多关键词批量爬虫初始化
        :param keywords: 行业关键词列表
        :param region: 城市名称
        :param ak: API密钥
        :param target_count_per_keyword: 每个关键词的目标爬取条数
        """
        self.session = requests.Session()
        self.keywords = keywords  # 多关键词列表
        self.region = region
        self.ak = ak
        self.target_count_per_keyword = target_count_per_keyword  # 每个关键词目标条数
        self.total_count = 0  # 所有关键词累计爬取条数
        self.page_size = 20  # 每页固定20条
        # 去重用：存储已爬取的店铺名称+地址（避免重复）
        self.crawled_shops = set()
        # 统一CSV文件名（城市_关键词组合_poi.csv）
        keyword_str = "_".join(self.keywords)
        self.csv_filename = f"{self.region}_{keyword_str}_poi.csv"
        # 初始化CSV
        self.init_csv()

    def init_csv(self):
        """初始化CSV文件，写入表头"""
        with open(self.csv_filename, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["关键词", "店铺名称", "地址", "省份", "城市", "区县", "电话"])
        print(f"已创建统一CSV文件：{self.csv_filename}")
        print(f"本次爬取关键词：{', '.join(self.keywords)}，每个关键词目标{self.target_count_per_keyword}条\n")

    def parse_single_keyword(self, keyword):
        """爬取单个关键词的POI数据"""
        current_count = 0  # 该关键词已爬条数
        max_page = math.ceil(self.target_count_per_keyword / self.page_size)
        print(f"===== 开始爬取关键词【{keyword}】=====")

        for page in range(max_page):
            # 已爬够该关键词目标条数，提前终止
            if current_count >= self.target_count_per_keyword:
                print(f"关键词【{keyword}】已爬够{self.target_count_per_keyword}条，停止爬取\n")
                break

            try:
                # 构造请求URL
                url = (
                    "https://api.map.baidu.com/place/v2/search"
                    "?query={query}"
                    "&region={region}"
                    "&output=json"
                    "&ak={ak}"
                    "&page_size={page_size}"
                    "&page_num={page}"
                ).format(
                    query=keyword,
                    region=self.region,
                    ak=self.ak,
                    page_size=self.page_size,
                    page=page
                )
                # 随机延迟防反爬
                time.sleep(random.uniform(1, 2))
                response = self.session.get(url)
                response.raise_for_status()
                # 解析数据，返回本页新增条数（去重后）
                page_add_count = self.parse_response_data(response.json(), keyword)
                current_count += page_add_count

                if page_add_count > 0:
                    print(f"关键词【{keyword}】第{page + 1}页：新增{page_add_count}条，累计{current_count}条")
                else:
                    # 本页无新数据，说明该关键词已爬完所有数据
                    print(f"关键词【{keyword}】第{page + 1}页：无新数据，停止爬取\n")
                    break

            except Exception as e:
                print(f"关键词【{keyword}】第{page + 1}页爬取失败: {str(e)}\n")
                continue

        # 更新总条数
        self.total_count += current_count
        return current_count

    def parse_response_data(self, response, keyword):
        """解析数据，去重后写入CSV，返回本页新增条数"""
        if response.get("status") != 0:
            print(f"⚠️ 接口返回错误: {response.get('message')}")
            return 0

        data_list = response.get("results", [])
        if not data_list:
            return 0

        page_add_count = 0  # 本页新增（去重后）条数
        # 计算该关键词还需要爬的条数
        need_count = self.target_count_per_keyword - (self.total_count + page_add_count)

        with open(self.csv_filename, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            for data in data_list:
                if need_count <= 0:
                    break

                # 提取核心信息
                name = data.get("name", "无名称")
                address = data.get("address", "无地址")
                province = data.get("province", "无省份")
                city = data.get("city", "无城市")
                area = data.get("area", "无区县")
                telephone = data.get("telephone", "无电话")

                # 生成唯一标识（名称+地址）用于去重
                shop_unique_key = f"{name}_{address}"
                if shop_unique_key not in self.crawled_shops:
                    # 写入数据（增加“关键词”列，方便区分来源）
                    writer.writerow([keyword, name, address, province, city, area, telephone])
                    self.crawled_shops.add(shop_unique_key)
                    page_add_count += 1
                    need_count -= 1

        return page_add_count

    def start_batch_crawl(self):
        """启动批量爬取（遍历所有关键词）"""
        for idx, keyword in enumerate(self.keywords, 1):
            print(f"【{idx}/{len(self.keywords)}】开始处理关键词：{keyword}")
            self.parse_single_keyword(keyword)
            # 关键词之间增加稍长延迟，降低API调用频率
            if idx < len(self.keywords):
                time.sleep(3)

        print(f"\n===== 批量爬取完成 =====\n所有关键词累计爬取（去重后）：{self.total_count}条")
        print(f"数据文件保存为：{self.csv_filename}")


if __name__ == "__main__":
    YOUR_BAIDU_AK = "9EBJCfeQw2hXs04Ey2QqH3yKpMa3RI6K"

    print("===== 百度地图POI爬虫（多关键词批量版） =====")
    # 1. 输入城市（非空校验）
    while True:
        region_input = input("请输入要爬取的城市：").strip()
        if region_input:
            break
        print("❌ 城市名称不能为空，请重新输入！")

    # 2. 输入多个关键词（逗号分隔，非空校验）
    while True:
        keywords_input = input("请输入行业或相关关键词：").strip()
        if keywords_input:
            # 拆分关键词，去除空格，去重
            keywords_list = [k.strip() for k in keywords_input.split(",") if k.strip()]
            if keywords_list:
                break
            print("❌ 关键词不能为空，请重新输入")
        else:
            print("❌ 关键词不能为空，请重新输入！")

    # 3. 输入每个关键词的目标条数（数字校验）
    while True:
        try:
            count_input = int(input("请输入每个关键词的目标条数（建议≤300）：").strip())
            if count_input > 0:
                break
            print("❌ 条数必须是大于0的数字，请重新输入！")
        except ValueError:
            print("❌ 请输入有效的数字（如100、200）！")

    # 启动批量爬虫
    spider = MultiKeywordSpider(
        keywords=keywords_list,
        region=region_input,
        ak=YOUR_BAIDU_AK,
        target_count_per_keyword=count_input
    )
    spider.start_batch_crawl()