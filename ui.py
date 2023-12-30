# -*- coding: utf-8 -*-
# @Time     :2023/12/31 1:09
# @Author   :ym
# @Email    :49154181@qq.com
# @File     :ui.py
# @Software :PyCharm
import ssl
import json
import time
import uuid
import random
import asyncio
import threading
import subprocess
import tkinter as tk
from loguru import logger
from datetime import datetime
from tkinter import scrolledtext, messagebox
from websockets_proxy import Proxy, proxy_connect


def get_datetime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def insert_log(log_widget, content, tag):
    log_widget.insert(tk.END, content, tag)
    log_widget.see(tk.END)


async def connect_to_wss(user_id, socks5_proxy, log_widget):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, f'{socks5_proxy}-{user_id}'))
    logger.info(device_id)
    insert_log(log_widget, f"{get_datetime()} user_id: {user_id}\n", 'info')
    insert_log(log_widget, f"{get_datetime()} device_id: {device_id}\n", 'info')

    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy.wynd.network:4650/"
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(send_message)
                        insert_log(log_widget, f"{get_datetime()} send_message: {send_message}\n", 'info')
                        await websocket.send(send_message)
                        await asyncio.sleep(20)

                asyncio.create_task(send_ping())
                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(message)
                    insert_log(log_widget, f"{get_datetime()} message: {message}\n", 'info')

                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "2.5.0"
                            }
                        }
                        logger.debug(auth_response)

                        insert_log(log_widget, f"{get_datetime()} auth_response: {auth_response}\n", 'info')

                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(pong_response)
                        insert_log(log_widget, f"{get_datetime()} pong_response: {pong_response}\n", 'info')

                        await websocket.send(json.dumps(pong_response))

        except Exception as e:
            insert_log(log_widget, f"{get_datetime()} error: {e}\n", 'error')
            insert_log(log_widget, f"{get_datetime()} error: {socks5_proxy}\n", 'error')


def start_operation():
    user_id = user_id_entry.get()
    proxy_list = proxy_list_entry.get()
    asyncio.run_coroutine_threadsafe(connect_to_wss(user_id, proxy_list, log_box), new_loop)


def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?\n"):
        root.destroy()


def run_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def open_github(event):
    url = "https://github.com/ymmmmmmmm/getgrass_bot"
    subprocess.Popen(['start', url], shell=True)


def open_referral(event):
    url = "https://app.getgrass.io/register/?referralCode=0PhrIR8TAQX6IG4"
    subprocess.Popen(['start', url], shell=True)


if __name__ == '__main__':
    new_loop = asyncio.new_event_loop()
    root = tk.Tk()
    root.title("Grass")

    tk.Label(root, text="User ID:").pack()
    user_id_entry = tk.Entry(root, width=50)
    user_id_entry.pack()

    tk.Label(root, text="Socks5 Proxy:").pack()
    proxy_list_entry = tk.Entry(root, width=50)
    proxy_list_entry.pack()

    start_button = tk.Button(root, text="开始操作", command=start_operation)
    start_button.pack()

    log_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=15, width=130)
    log_box.pack(padx=10, pady=10)
    log_box.tag_configure('info', foreground='blue')
    log_box.tag_configure('warning', foreground='orange')
    log_box.tag_configure('error', foreground='red')

    labels_frame = tk.Frame(root)

    github_label = tk.Label(labels_frame, text="GitHub Repository: https://github.com/ymmmmmmmm/getgrass_bot    ",
                            fg="blue")
    github_label.pack(side=tk.LEFT)

    referral_label = tk.Label(labels_frame,
                              text="Referral Link: https://app.getgrass.io/register/?referralCode=0PhrIR8TAQX6IG4",
                              fg="red")
    referral_label.pack(side=tk.LEFT)

    github_label.bind("<Button-1>", open_github)
    referral_label.bind("<Button-1>", open_referral)
    labels_frame.pack()
    log_box.insert(tk.END, '请按照提示输入正确的user_id\n', 'info')
    log_box.insert(tk.END, 'Socks5 Proxy格式为 socks5://用户名:密码@ip:端口\n', 'info')

    asyncio_loop_thread = threading.Thread(target=run_asyncio_loop, args=(new_loop,), daemon=True)
    asyncio_loop_thread.start()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
