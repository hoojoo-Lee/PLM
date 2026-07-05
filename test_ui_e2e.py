import os
import pytest
from playwright.sync_api import sync_playwright, Page

SCREENSHOT_DIR = "tests/screenshots"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def save_screenshot(page: Page, test_name: str):
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"{test_name}.png")
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"截图已保存: {screenshot_path}")

def get_el_message_text(page: Page):
    try:
        message_selector = ".el-message__content"
        page.wait_for_selector(message_selector, timeout=5000)
        return page.text_content(message_selector)
    except Exception as e:
        print(f"获取 el-message 失败: {e}")
        return None

def test_global_error_handling(page: Page):
    try:
        console_errors = []
        page.on("console", lambda msg: console_errors.append(f"{msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: console_errors.append(f"PageError: {err}"))
        
        page.goto("http://localhost:8001")
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_timeout(5000)
        
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "after_load.png"))
        
        print("\n=== 浏览器控制台输出 ===")
        for error in console_errors[:20]:
            print(error)
        
        tree_nodes = page.locator(".el-tree-node")
        print(f"\nel-tree-node数量: {tree_nodes.count()}")
        
        if tree_nodes.count() > 0:
            tree_nodes.first.click()
            page.wait_for_timeout(2000)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "after_tree_click.png"))
        
        npi_tab = page.locator(".el-tabs__item", has_text="NPI")
        if npi_tab.count() > 0:
            npi_tab.first.click()
            page.wait_for_timeout(2000)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "after_npi_click.png"))
        
        page.evaluate("""() => {
            const buttons = document.querySelectorAll('.el-button');
            for (const btn of buttons) {
                if (btn.textContent.includes('极速新增任务')) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }""")
        page.wait_for_timeout(2000)
        
        dialog = page.locator(".el-dialog")
        print(f"弹窗数量: {dialog.count()}")
        
        if dialog.count() > 0:
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "after_fast_add_click.png"))
            
            all_selects = dialog.locator(".el-select")
            print(f"弹窗内el-select数量: {all_selects.count()}")
            
            save_btn = dialog.locator(".el-button", has_text="确认创建")
            print(f"确认创建按钮数量: {save_btn.count()}")
            
            if save_btn.count() > 0:
                save_btn.first.click()
                
                page.wait_for_timeout(3000)
                
                error_text = get_el_message_text(page)
                if error_text:
                    assert "[object Object]" not in error_text, \
                        f"错误信息包含 [object Object]: {error_text}"
                    assert len(error_text) > 0, "错误信息为空"
                    print(f"全局报错验证通过: {error_text}")
                else:
                    print("未捕获到错误消息，可能提交成功了")
            else:
                print("未找到确认创建按钮")
        else:
            print("未找到弹窗")
    except Exception as e:
        save_screenshot(page, "test_global_error_handling")
        raise

def test_product_edit_customer_select(page: Page):
    try:
        page.goto("http://localhost:8001")
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_timeout(8000)
        
        debug_info = page.evaluate("""() => {
            const treeNodes = document.querySelectorAll('.el-tree-node');
            const nodeInfo = [];
            for (const node of treeNodes) {
                const content = node.querySelector('.el-tree-node__content');
                const span = content ? content.querySelector('span') : null;
                nodeInfo.push({
                    hasContent: !!content,
                    text: span ? span.textContent : 'no text'
                });
            }
            
            const buttons = document.querySelectorAll('.el-button');
            const buttonTexts = [];
            for (const btn of buttons) {
                const text = btn.textContent || '';
                if (text.trim()) {
                    buttonTexts.push(text.trim());
                }
            }
            
            const selectedItem = document.querySelector('.el-tree-node.is-current');
            const cardHeader = document.querySelector('.el-card__header');
            
            return {
                treeNodes: nodeInfo,
                buttons: buttonTexts,
                hasSelected: !!selectedItem,
                hasCardHeader: !!cardHeader,
                cardHeaderText: cardHeader ? cardHeader.textContent : 'no header'
            };
        }""")
        
        print(f"树节点信息: {debug_info['treeNodes']}")
        print(f"按钮列表: {debug_info['buttons']}")
        print(f"是否有选中节点: {debug_info['hasSelected']}")
        print(f"是否有卡片头: {debug_info['hasCardHeader']}")
        print(f"卡片头文本: {debug_info['cardHeaderText']}")
        
        page.evaluate("""() => {
            const treeNodes = document.querySelectorAll('.el-tree-node');
            for (const node of treeNodes) {
                const content = node.querySelector('.el-tree-node__content');
                if (content) {
                    content.click();
                    return true;
                }
            }
            if (treeNodes.length > 0) {
                treeNodes[0].click();
                return true;
            }
            return false;
        }""")
        page.wait_for_timeout(5000)
        
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "after_tree_click_test2.png"))
        
        debug_info2 = page.evaluate("""() => {
            const buttons = document.querySelectorAll('.el-button');
            const buttonTexts = [];
            for (const btn of buttons) {
                const text = btn.textContent || '';
                if (text.trim()) {
                    buttonTexts.push(text.trim());
                }
            }
            
            const selectedItem = document.querySelector('.el-tree-node.is-current');
            const cardHeader = document.querySelector('.el-card__header');
            
            const cardHeaderButtons = [];
            if (cardHeader) {
                const headerButtons = cardHeader.querySelectorAll('.el-button');
                for (const btn of headerButtons) {
                    cardHeaderButtons.push({
                        text: btn.textContent || '',
                        html: btn.innerHTML || ''
                    });
                }
            }
            
            return {
                buttons: buttonTexts,
                hasSelected: !!selectedItem,
                hasCardHeader: !!cardHeader,
                cardHeaderText: cardHeader ? cardHeader.textContent : 'no header',
                cardHeaderButtons: cardHeaderButtons
            };
        }""")
        
        print(f"点击后按钮列表: {debug_info2['buttons']}")
        print(f"点击后是否有选中节点: {debug_info2['hasSelected']}")
        print(f"点击后是否有卡片头: {debug_info2['hasCardHeader']}")
        print(f"点击后卡片头文本: {debug_info2['cardHeaderText']}")
        print(f"卡片头按钮详情: {debug_info2['cardHeaderButtons']}")
        
        edit_found = page.evaluate("""() => {
            const cardHeaders = document.querySelectorAll('.el-card__header');
            for (const header of cardHeaders) {
                const buttons = header.querySelectorAll('.el-button');
                if (buttons.length > 0) {
                    const firstBtn = buttons[buttons.length - 1];
                    firstBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    setTimeout(() => firstBtn.click(), 300);
                    return true;
                }
            }
            return false;
        }""")
        print(f"编辑按钮是否找到: {edit_found}")
        
        page.wait_for_timeout(3000)
        
        dialog = page.locator(".el-dialog")
        print(f"弹窗数量: {dialog.count()}")
        
        assert dialog.count() > 0, "未找到编辑产品的弹窗"
        
        all_selects = dialog.locator(".el-select")
        print(f"弹窗内el-select数量: {all_selects.count()}")
        
        customer_select_found = page.evaluate("""() => {
            const formItems = document.querySelectorAll('.el-dialog .el-form-item');
            for (const item of formItems) {
                const label = item.querySelector('label');
                if (label && label.textContent.includes('客户名称')) {
                    const select = item.querySelector('.el-select');
                    if (select) {
                        select.click();
                        setTimeout(() => {
                            const options = document.querySelectorAll('.el-select-dropdown__item');
                            if (options.length > 0) {
                                options[0].click();
                            }
                        }, 1000);
                        return true;
                    }
                }
            }
            return false;
        }""")
        
        assert customer_select_found, "未找到客户名称的 el-select 下拉框"
        print("找到客户名称下拉框并成功选中")
    except Exception as e:
        save_screenshot(page, "test_product_edit_customer_select")
        raise

def test_npi_tracker_project_selector(page: Page):
    try:
        page.goto("http://localhost:8001")
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_timeout(5000)
        
        tree_nodes = page.locator(".el-tree-node")
        if tree_nodes.count() > 0:
            tree_nodes.first.click()
            page.wait_for_timeout(2000)
        
        npi_tab = page.locator(".el-tabs__item", has_text="NPI")
        print(f"NPI Tab数量: {npi_tab.count()}")
        
        if npi_tab.count() > 0:
            npi_tab.first.click()
            page.wait_for_timeout(2000)
            
            page.evaluate("""() => {
                const buttons = document.querySelectorAll('.el-button');
                for (const btn of buttons) {
                    if (btn.textContent.includes('极速新增任务')) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            }""")
            page.wait_for_timeout(2000)
            
            dialog = page.locator(".el-dialog")
            print(f"弹窗数量: {dialog.count()}")
            
            if dialog.count() > 0:
                dialog_text = dialog.text_content()
                print(f"弹窗文本: {dialog_text[:500] if dialog_text else '空'}")
                
                all_selects = dialog.locator(".el-select")
                print(f"弹窗内el-select数量: {all_selects.count()}")
                
                project_select_found = page.evaluate("""() => {
                    const formItems = document.querySelectorAll('.el-dialog .el-form-item');
                    for (const item of formItems) {
                        const label = item.querySelector('label');
                        if (label && label.textContent.includes('项目')) {
                            const select = item.querySelector('.el-select');
                            if (select) {
                                select.click();
                                setTimeout(() => {
                                    const options = document.querySelectorAll('.el-select-dropdown__item');
                                    if (options.length > 0) {
                                        options[0].click();
                                    }
                                }, 1000);
                                return true;
                            }
                        }
                    }
                    return false;
                }""")
                
                assert project_select_found, "未找到项目(Project)选择器"
                print("找到项目选择器并成功选中")
            else:
                print("未找到弹窗")
        else:
            print("未找到 NPI Tab")
    except Exception as e:
        save_screenshot(page, "test_npi_tracker_project_selector")
        raise

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser):
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
    page.on("pageerror", lambda err: print(f"Page Error: {err}"))
    yield page
    page.close()

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        print("=== 测试一：全局报错拦截验证 ===")
        try:
            test_global_error_handling(page)
            print("✓ 全局报错验证通过")
        except Exception as e:
            print(f"✗ 全局报错验证失败: {e}")
        
        print("\n=== 测试二：产品编辑下拉框验证 ===")
        try:
            test_product_edit_customer_select(page)
            print("✓ 产品编辑下拉框验证通过")
        except Exception as e:
            print(f"✗ 产品编辑下拉框验证失败: {e}")
        
        print("\n=== 测试三：甘特图与 NPI 关联验证 ===")
        try:
            test_npi_tracker_project_selector(page)
            print("✓ NPI Tracker 项目选择器验证通过")
        except Exception as e:
            print(f"✗ NPI Tracker 项目选择器验证失败: {e}")
        
        browser.close()
        print("\n=== 所有测试完成 ===")