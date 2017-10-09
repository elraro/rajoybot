import telebot
import requests
import sys
import time
import string
from os import environ

import telebot.types as types

if environ.get('TOKEN') is not None:
    token = environ.get('TOKEN')
else:
    print("You need to create the container with \"-e TOKEN=YOURBOTTOKEN\"")
    exit()
bot = telebot.TeleBot(token)
remove = string.punctuation + string.whitespace

sounds = [["http://rajoy.elraro.eu/sonido0.ogg", "Cuanto peor mejor para todos",
           "cuanto peor mejor para todos y cuanto peor para todos mejor, mejor para mi el suyo beneficio politico"],
          ["http://rajoy.elraro.eu/sonido1.ogg", "Es el alcalde",
           "es el vecino el que elige el alcalde y es el alcalde el que quiere que sean los vecinos el alcalde"],
          ["http://rajoy.elraro.eu/sonido2.ogg", "Pues... eh... ¿Y la europea?",
           "pues... eh... ¿Y la europea?"],
          ["http://rajoy.elraro.eu/sonido3.ogg", "La segunda ya tal",
           "l segunda ya tal"],
          ["http://rajoy.elraro.eu/sonido4.ogg", "Me gusta Cataluña",
           "me gusta cataluña. me gustan sus gentes, su caracter abierto, su laboriosidad, son emprendedores, hacen cosas"],
          ["http://rajoy.elraro.eu/sonido5.ogg", "Me ha pasado una cosa",
           "me ha pasado una cosa verdaderamente notable: que lo he escrito aqui, y no entiendo mi letra"],
          ["http://rajoy.elraro.eu/sonido6.ogg", "ETA es una gran nacion",
           "quiero transmitir a los españoles un mensaje de esperanza. eta es una gran nacion"],
          ["http://rajoy.elraro.eu/sonido7.ogg", "Somos sentimientos",
           "somos sentimientos y tenemos seres humanos"],
          ["http://rajoy.elraro.eu/sonido8.ogg", "Los españoles muy españoles",
           "españa es una gran nacion y los españoles muy españoles y mucho españoles"],
          ["http://rajoy.elraro.eu/sonido9.ogg", "Lo que nosotros hemos hecho",
           "lo que nosotros hemos hecho, cosa que no hizo usted, es en... engañar a la gente"],
          ["http://rajoy.elraro.eu/sonido10.ogg", "Viva el vino",
           "viva el vino"],
          ["http://rajoy.elraro.eu/sonido11.ogg", "La ceramica de Talavera",
           "la ceramica de talavera no es cosa menor, dicho de otra forma: es cosa mayor"],
          ["http://rajoy.elraro.eu/sonido12.ogg", "No es cierto",
           "no es cierto. salvo alguna cosa que es lo que han publicado algunos medios de comunicacion"],
          ["http://rajoy.elraro.eu/sonido13.ogg", "Lo unico serio",
           "lo unico serio al final en la vida es ser serio"],
          ["http://rajoy.elraro.eu/sonido14.ogg", "Ser solidario",
           "una cosa es ser solidario y otra cosa es serlo a cambio de nada"],
          ["http://rajoy.elraro.eu/sonido15.ogg", "Maquina-inception",
           "hay que fabricar maquinas que nos permita seguir fabricando maquinas, porque lo que no va a hacer nunca la maquina es fabricar maquinas"],
          ["http://rajoy.elraro.eu/sonido16.ogg", "Dentro de 300 años",
           "¿como alguien puede decir lo que va a pasar en el mundo dentro de 300 años?"],
          ["http://rajoy.elraro.eu/sonido17.ogg", "Agua que cae del cielo",
           "esto no es como el agua que cae del cielo sin que se sepa exactamente por que"],
          ["http://rajoy.elraro.eu/sonido18.ogg", "No mas IVA",
           "no mas IVA', esto es un clamor que recorre España de arriba a abajo y de abajo a arriba"],
          ["http://rajoy.elraro.eu/sonido19.ogg", "Bajar los impuestos",
           "dije que bajaria los impuestos y los estoy subiendo"],
          ["http://rajoy.elraro.eu/sonido20.ogg", "Hilitos de na",
           "se piensa que el fuel esta aun enfriandose, salen unos pequeños hilitos"]]


@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    bot.send_message(cid,
                     "Este bot es inline. Teclea su nombre en una conversación/grupo y podras enviar un mensaje de nuestro querido presidente del gobierno.")
    bot.send_message(cid,
                     "Creado por @elraro . Puedes mejorarme en la siguiente dirección: https://github.com/elraro/rajoyBot")

@bot.inline_handler(lambda query: query.query == '')
def query_empty(inline_query):
    r = []
    for i, sound in enumerate(sounds):
        r.append(types.InlineQueryResultVoice(str(i), sound[0], sound[1], voice_duration=7))
    bot.answer_inline_query(inline_query.id, r)

@bot.inline_handler(lambda query: query.query)
def query_text(inline_query):
    try:
        text = inline_query.query.translate(remove).lower()
        r = []
        for i, sound in enumerate(sounds):
            if text in sound[2]:
                r.append(types.InlineQueryResultVoice(str(i), sound[0], sound[1]))
        bot.answer_inline_query(inline_query.id, r)
    except Exception as e:
        print(e)


while True:
    try:
        bot.polling(none_stop=True)
    except requests.exceptions.ConnectionError as e:
        print(sys.stderr, str(e))
        time.sleep(30)
