import requests
import json
import os
# -------------------------------------------------------------------------------------------
# github workflows
# -------------------------------------------------------------------------------------------
if __name__ == '__main__':
    # pushplus秘钥 申请地址 http://www.pushplus.plus
    sckey = os.environ.get("PUSHPLUS", "")

    # 推送内容
    title = "Glados"
    success, fail = 0, 0        # 成功账号数量 失败账号数量
    sendContent = ""

    # glados账号cookie，多账号用 & 分隔
    cookies = [c.strip() for c in os.environ.get("COOKIES", "").split("&") if c.strip()]
    if not cookies:
        print('未获取到COOKIE变量')
        exit(0)

    url = "https://glados.rocks/api/user/checkin"
    url2 = "https://glados.rocks/api/user/status"

    referer = 'https://glados.rocks/console/checkin'
    origin = "https://glados.rocks"
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    payload = {
        'token': 'glados.one'
    }

    for idx, cookie in enumerate(cookies, 1):
        email = ""
        message_status = "签到失败，请检查..."
        message_days = "获取信息失败"
        try:
            headers = {'cookie': cookie, 'referer': referer, 'origin': origin, 'user-agent': useragent}
            checkin = requests.post(url, headers=dict(headers, **{'content-type': 'application/json;charset=UTF-8'}),
                                    data=json.dumps(payload), timeout=30)
            state = requests.get(url2, headers=headers, timeout=30)

            # 账号状态。cookie 失效时返回里没有 data 字段，不能直接 result['data'] 取值崩溃
            if state.status_code == 200:
                data = state.json().get('data') or {}
                email = data.get('email') or "未知账号"
                leftdays = data.get('leftDays')
                if leftdays is not None:
                    message_days = f"{int(float(leftdays))} 天"
                else:
                    message_days = "无法获取剩余天数（cookie 可能失效）"

            # 签到结果。GLaDOS 已改为积分制：
            #   code 0 = 本次签到成功（+积分）
            #   code 1 = 今天已登记过，message 形如 "Today's observation logged..."
            #   其他   = 异常（如 -2 没有权限，即 cookie 失效）
            # 兼容旧版消息 'Checkin! Get 1 Day' / 'Please Try Tomorrow'
            if checkin.status_code == 200:
                result = checkin.json()
                code = result.get('code')
                message = result.get('message') or ""
                if code == 0 or message == "Checkin! Get 1 Day":
                    success += 1
                    points = result.get('points')
                    message_status = "签到成功" + (f"，+{points} 分" if points else "")
                elif code == 1 or message == "Please Try Tomorrow" or "observation logged" in message:
                    success += 1
                    message_status = "今日已签到"
                else:
                    fail += 1
                    message_status = f"签到失败: {message or result}"
            else:
                fail += 1
                message_status = f"签到请求失败 HTTP {checkin.status_code}（cookie 可能失效）"
        except Exception as e:
            fail += 1
            message_status = f"处理出错: {e}"

        # 推送内容
        sendContent += f"{'-'*30}\n\
            账号{idx}: {email}\n\
            签到情况: {message_status}\n\
            剩余天数: {message_days}\n"

    sendContent += '-' * 30
    print("sendContent:" + "\n", sendContent)
    if sckey != "":
        title += f': 成功{success},失败{fail}'
        plusurl = f"http://www.pushplus.plus/send?token={sckey}&title={title}&content={sendContent}"
        r = requests.get(plusurl)
        print(r.status_code)
