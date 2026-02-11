# 设置控制台输出编码为 utf-8，防止中文乱码
import io
import logging
import sys

from collectors import RSSCollector, WebScraperCollector

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

try:
    print("=" * 60)
    print("开始测试中文数据源抓取")
    print("=" * 60)

    # 测试 RSS 收集器（机器之心）
    print("\n【1/2】测试 RSS 收集器（机器之心）...")
    rss_collector = RSSCollector("sources.yaml")
    rss_items = rss_collector.collect()
    jqzx_items = [i for i in rss_items if i.source == "机器之心"]

    if jqzx_items:
        print(f"✓ 机器之心: 成功抓取 {len(jqzx_items)} 条")
        print(f"  示例标题: {jqzx_items[0].title}")
        print(f"  示例链接: {jqzx_items[0].url}")
        print(f"  权威度评分: {jqzx_items[0].raw_score}")
    else:
        print("✗ 机器之心: 未抓取到文章")

    # 测试 Web 爬虫收集器（量子位）
    print("\n【2/2】测试 Web 爬虫收集器（量子位）...")
    web_collector = WebScraperCollector("sources.yaml")
    web_items = web_collector.collect()
    lzw_items = [i for i in web_items if i.source == "量子位"]

    if lzw_items:
        print(f"✓ 量子位: 成功抓取 {len(lzw_items)} 条")
        print(f"  示例标题: {lzw_items[0].title}")
        print(f"  示例链接: {lzw_items[0].url}")
        print(f"  发布时间: {lzw_items[0].published_at.strftime('%Y-%m-%d')}")
        if lzw_items[0].content:
            print(f"  内容摘要: {lzw_items[0].content[:100]}...")
    else:
        print("✗ 量子位: 未抓取到文章")

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    jqzx_success = len(jqzx_items) > 0
    lzw_success = len(lzw_items) > 0

    print(f"机器之心: {'✓ 通过' if jqzx_success else '✗ 失败'} ({len(jqzx_items)} 条)")
    print(f"量子位:   {'✓ 通过' if lzw_success else '✗ 失败'} ({len(lzw_items)} 条)")

    if jqzx_success and lzw_success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败")

except Exception as e:
    print(f"发生错误: {e}")
    import traceback

    traceback.print_exc()
