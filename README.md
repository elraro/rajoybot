# RajoyBot "Somos sentimientos y tenemos seres humanos"

[![Docker Build Action](https://github.com/elraro/rajoyBot/actions/workflows/docker.yml/badge.svg)](https://github.com/elraro/rajoyBot/actions/workflows/docker.yml) [![Docker Build Status](https://img.shields.io/docker/pulls/elraro/rajoybot)](https://hub.docker.com/r/elraro/rajoybot)

Bot de Telegram con frases de nuestro querido ex-presidente Mariano Rajoy Brey.

Es necesario modificar TELEGRAM_BOT_TOKEN dentro del fichero [docker-compose.yml](../blob/master/docker-compose.yml)
También es recomendable modificar TELEGRAM_USER_ALIAS con vuestro alias de Telegram, para que sólo vosotros podáis ver las estadísticas.

```
docker-compose up
```
