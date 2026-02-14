import logging
import os
import sys

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 添加当前目录到系统路径，以便导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 解决 Windows 控制台输出编码问题
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from collectors import WebScraperCollector
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保 collectors.py 和 models.py 在同一目录下")
    sys.exit(1)

def test_qbitai_scraping():
    sources_path = os.path.join(current_dir, "sources.yaml")

    if not os.path.exists(sources_path):
        print(f"错误: 配置文件未找到: {sources_path}")
        return

    print(f"正在初始化采集器，配置文件: {sources_path}")
    collector = WebScraperCollector(sources_path)

    print("开始从量子位 (QbitAI) 抓取内容...")
    try:
        # 执行抓取
        items = collector.collect()

        # 过滤量子位的内容（以防 sources.yaml 中有其他网站）
        qbit_items = [i for i in items if "量子位" in i.source or "qbitai" in i.url]

        if not qbit_items:
            print("未抓取到量子位的内容。请检查网络连接或选择器配置。")
            return

        print(f"\n成功抓取 {len(qbit_items)} 条内容：")
        print("=" * 60)

        # 简单去重 (以防 .swiper-slide a 和 h4 a 抓取了相同的内容)
        seen_titles = set()
        unique_items = []
        for item in qbit_items:
            if item.title not in seen_titles:
                unique_items.append(item)
                seen_titles.add(item.title)

        for i, item in enumerate(unique_items, 1):
            print(f"[{i}] 标题: {item.title}")
            print(f"    链接: {item.url}")
            print(f"    发布时间: {item.published_at}")
            # 简单的内容摘要展示
            summary = item.content[:100].replace('\n', ' ') + "..." if item.content else "(无内容摘要)"
            print(f"    摘要: {summary}")
            print("-" * 60)

    except Exception as e:
        print(f"抓取过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qbitai_scraping()
