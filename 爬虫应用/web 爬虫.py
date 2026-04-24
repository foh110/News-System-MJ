from selenium import webdriver
from selenium.webdriver.edge.options import Options  # 替换为Edge的Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time
import random


class WoSEdgeSpider:
    def __init__(self, username, password, keywords, target_count):
        self.username = username
        self.password = password
        self.keywords = keywords
        self.target_count = target_count
        self.current_count = 0
        self.csv_filename = "wos_papers_edge.csv"
        # 初始化Edge浏览器（核心替换部分）
        self.edge_options = Options()
        # 隐藏自动化特征（和Chrome一致，适配Edge）
        self.edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.edge_options.add_experimental_option('useAutomationExtension', False)
        self.edge_options.add_argument("--blink-settings=imagesEnabled=false")  # 禁用图片
        self.edge_options.add_argument("--start-maximized")  # 最大化窗口
        self.edge_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.91")  # Edge UA

        # 初始化EdgeDriver（关键：指定msedgedriver路径，若放代码文件夹可省略executable_path）
        self.driver = webdriver.Edge(
            executable_path="msedgedriver.exe",  # 驱动和代码同文件夹，直接写文件名
            options=self.edge_options
        )  # 若Driver不在环境变量，加executable_path="msedgedriver.exe"
        self.driver.implicitly_wait(10)
        # 移除webdriver标识（防反爬）
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.init_csv()

    def init_csv(self):
        """初始化CSV（和之前一致）"""
        with open(self.csv_filename, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["关键词", "标题", "作者", "发表年份", "期刊"])
        print(f"初始化CSV：{self.csv_filename}")

    def login(self):
        """模拟登录WoS（仅替换浏览器，定位器和之前一致）"""
        try:
            self.driver.get("https://www.webofscience.com/")
            time.sleep(2)
            # 点击登录按钮（替换为你复制的XPATH）
            login_btn = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Sign In')]"))
            )
            login_btn.click()
            time.sleep(3)

            # 输入账号（替换XPATH）
            username_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='username']"))
            )
            username_input.send_keys(self.username)
            time.sleep(1)

            # 输入密码（替换XPATH）
            password_input = self.driver.find_element(By.XPATH, "//input[@id='password']")
            password_input.send_keys(self.password)
            time.sleep(1)

            # 点击登录（替换XPATH）
            self.driver.find_element(By.XPATH, "//button[@id='login']").click()
            time.sleep(5)

            if "Welcome" in self.driver.page_source:
                print("✅ Edge登录WoS成功！")
            else:
                print("❌ 登录失败，检查账号/XPATH！")
        except Exception as e:
            print(f"登录报错：{str(e)}")
            self.driver.quit()
            raise

    def search_keyword(self, keyword):
        """搜索+解析（逻辑和之前完全一致）"""
        try:
            # 定位搜索框（替换XPATH）
            search_box = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='search-input']"))
            )
            search_box.clear()
            search_box.send_keys(f"TI={keyword}")
            time.sleep(2)
            # 点击搜索（替换XPATH）
            self.driver.find_element(By.XPATH, "//button[contains(text(), 'Search')]").click()
            time.sleep(5)

            page = 1
            while self.current_count < self.target_count:
                # 等待论文列表加载（替换XPATH）
                paper_elems = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@class='hit-list-item']"))
                )
                if not paper_elems:
                    print(f"关键词【{keyword}】第{page}页无数据")
                    break

                # 解析本页数据
                paper_count = self.parse_page(paper_elems, keyword)
                print(f"关键词【{keyword}】第{page}页：新增{paper_count}条，累计{self.current_count}条")

                # 下一页（替换XPATH）
                try:
                    next_btn = self.driver.find_element(By.XPATH, "//button[@aria-label='Next page']")
                    if next_btn.is_enabled():
                        next_btn.click()
                        time.sleep(random.uniform(5, 7))
                        page += 1
                    else:
                        break
                except:
                    break
        except Exception as e:
            print(f"关键词【{keyword}】爬取失败：{str(e)}")

    def parse_page(self, paper_elems, keyword):
        """解析单页数据（逻辑不变）"""
        paper_count = 0
        with open(self.csv_filename, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            for elem in paper_elems:
                if self.current_count >= self.target_count:
                    break
                try:
                    title = elem.find_element(By.XPATH, ".//h3[@class='title']").text.strip()
                    authors = elem.find_element(By.XPATH, ".//div[@class='authors']").text.strip()
                    pub_year = elem.find_element(By.XPATH, ".//span[@class='pubyear']").text.strip()
                    journal = elem.find_element(By.XPATH, ".//span[@class='journal']").text.strip()
                    writer.writerow([keyword, title, authors, pub_year, journal])
                    self.current_count += 1
                    paper_count += 1
                except:
                    continue
        return paper_count

    def start_crawl(self):
        """启动爬取"""
        self.login()
        print(f"\n开始爬取关键词：{', '.join(self.keywords)}")
        for keyword in self.keywords:
            if self.current_count >= self.target_count:
                break
            self.search_keyword(keyword)
            time.sleep(random.uniform(7, 10))

        self.driver.quit()
        print(f"\n✅ 爬取完成！累计{self.current_count}条，文件：{self.csv_filename}")


if __name__ == "__main__":
    # 替换为你的WoS账号密码
    WO_USERNAME = "你的WoS账号"
    WO_PASSWORD = "你的WoS密码"

    print("===== WoS Edge浏览器爬虫 =====")
    keywords_input = input("请输入关键词（逗号分隔）：").strip()
    keywords_list = [k.strip() for k in keywords_input.split(",") if k.strip()]
    target_count = int(input("目标条数（≤50）：").strip())

    # 启动Edge爬虫
    spider = WoSEdgeSpider(
        username=WO_USERNAME,
        password=WO_PASSWORD,
        keywords=keywords_list,
        target_count=target_count
    )
    spider.start_crawl()