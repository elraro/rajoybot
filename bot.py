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

sounds = [["http://rajoy.elraro.eu/sound0.ogg", "Cuanto peor mejor para todos",
           "cuanto peor mejor para todos y cuanto peor para todos mejor, mejor para mi el suyo beneficio politico"],
          ["http://rajoy.elraro.eu/sound1.ogg", "Es el alcalde",
           "es el vecino el que elige el alcalde y es el alcalde el que quiere que sean los vecinos el alcalde"],
          ["http://rajoy.elraro.eu/sound2.ogg", "Pues... eh... ¿Y la europea?",
           "pues... eh... ¿Y la europea?"],
          ["http://rajoy.elraro.eu/sound3.ogg", "La segunda ya tal",
           "la segunda ya tal"],
          ["http://rajoy.elraro.eu/sound4.ogg", "Me gusta Cataluña",
           "me gusta cataluña. me gustan sus gentes, su caracter abierto, su laboriosidad, son emprendedores, hacen cosas"],
          ["http://rajoy.elraro.eu/sound5.ogg", "Me ha pasado una cosa",
           "me ha pasado una cosa verdaderamente notable: que lo he escrito aqui, y no entiendo mi letra"],
          ["http://rajoy.elraro.eu/sound6.ogg", "ETA es una gran nacion",
           "quiero transmitir a los españoles un mensaje de esperanza. eta es una gran nacion"],
          ["http://rajoy.elraro.eu/sound7.ogg", "Somos sentimientos",
           "somos sentimientos y tenemos seres humanos"],
          ["http://rajoy.elraro.eu/sound8.ogg", "Los españoles muy españoles",
           "españa es una gran nacion y los españoles muy españoles y mucho españoles"],
          ["http://rajoy.elraro.eu/sound9.ogg", "Lo que nosotros hemos hecho",
           "lo que nosotros hemos hecho, cosa que no hizo usted, es en... engañar a la gente"],
          ["http://rajoy.elraro.eu/sound10.ogg", "Viva el vino",
           "viva el vino"],
          ["http://rajoy.elraro.eu/sound11.ogg", "La ceramica de Talavera",
           "la ceramica de talavera no es cosa menor, dicho de otra forma: es cosa mayor"],
          ["http://rajoy.elraro.eu/sound12.ogg", "No es cierto",
           "no es cierto. salvo alguna cosa que es lo que han publicado algunos medios de comunicacion"],
          ["http://rajoy.elraro.eu/sound13.ogg", "Lo unico serio",
           "lo unico serio al final en la vida es ser serio"],
          ["http://rajoy.elraro.eu/sound14.ogg", "Ser solidario",
           "una cosa es ser solidario y otra cosa es serlo a cambio de nada"],
          ["http://rajoy.elraro.eu/sound15.ogg", "Maquina-inception",
           "hay que fabricar maquinas que nos permita seguir fabricando maquinas, porque lo que no va a hacer nunca la maquina es fabricar maquinas"],
          ["http://rajoy.elraro.eu/sound16.ogg", "Dentro de 300 años",
           "¿como alguien puede decir lo que va a pasar en el mundo dentro de 300 años?"],
          ["http://rajoy.elraro.eu/sound17.ogg", "Agua que cae del cielo",
           "esto no es como el agua que cae del cielo sin que se sepa exactamente por que"],
          ["http://rajoy.elraro.eu/sound18.ogg", "No mas IVA",
           "no mas IVA', esto es un clamor que recorre España de arriba a abajo y de abajo a arriba"],
          ["http://rajoy.elraro.eu/sound19.ogg", "Bajar los impuestos",
           "dije que bajaria los impuestos y los estoy subiendo"],
          ["http://rajoy.elraro.eu/sound20.ogg", "Hilitos de na",
           "se piensa que el fuel esta aun enfriandose, salen unos pequeños hilitos"],
          ["http://rajoy.elraro.eu/sound21.ogg", "Lo mejor para el próximo año 2016",
           "lo mejor para el proximo año 2016, que sinceramente falta nos hace a todos"],
          ["http://rajoy.elraro.eu/sound22.ogg", "Lo imposible",
           "y hare todo lo posible e incluso lo imposible, si tambien lo imposible es posible"],
          ["http://rajoy.elraro.eu/sound23.ogg", "Qué se puede hacer",
           "los gobernantes ya saben que se puede hacer, y que no se puede hacer"]]


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
        r.append(types.InlineQueryResultVoice(str(i), sound[0], sound[1]))
    bot.answer_inline_query(inline_query.id, r, cache_time=3600)

@bot.inline_handler(lambda query: query.query)
def query_text(inline_query):
    try:
        text = inline_query.query.translate(remove).lower()
        r = []
        for i, sound in enumerate(sounds):
            if text in sound[2]:
                r.append(types.InlineQueryResultVoice(str(i), sound[0], sound[1]))
        bot.answer_inline_query(inline_query.id, r, cache_time=3600)
    except Exception as e:
        print(e)


while True:
    try:
        bot.polling(none_stop=True)
    except requests.exceptions.ConnectionError as e:
        print(sys.stderr, str(e))
        time.sleep(30)
