#!/usr/bin/env python
# -*- coding: utf-8 -*-

from persistence.loggerfactory import LoggerFactory
from aiohttp import web
import telebot

LOG = LoggerFactory('RajoyBot.webhook').get_logger()


def start_webhook(bot, webhook_host, webhook_port, listening_ip, listening_port):
    LOG.info("Starting webhook on {}:{}".format(webhook_host, webhook_port))
    webhook_url_base = "https://{}:{}".format(webhook_host, webhook_port)
    webhook_url_path = "/{}/".format(bot.token)

    app = web.Application()

    # Process webhook calls
    async def handle(request):
        if request.match_info.get('token') == bot.token:
            request_body_dict = await request.json()
            update = telebot.types.Update.de_json(request_body_dict)
            bot.process_new_updates([update])
            return web.Response()
        else:
            return web.Response(status=403)

    app.router.add_post('/{token}/', handle)

    # Remove webhook, it fails sometimes the set if there is a previous webhook
    bot.remove_webhook()

    # Set webhook
    bot.set_webhook(url=webhook_url_base+webhook_url_path)

    # Start aiohttp server
    LOG.debug("Starting aiohttp on interface {}:{}".format(listening_ip, listening_port))
    web.run_app(
        app,
        host=listening_ip,
        port=listening_port
    )
