import random
from enum import Enum
from typing import Dict, Any

import requests
from emora_stdm import DialogueFlow
from emora_stdm import Macro, Ngrams
from typing import Dict, Any, List
import re

import openai
from emora_stdm import DialogueFlow
import utils
from utils import MacroGPTJSON, MacroNLG

PATH_USER_INFO = 'resource/userinfo.json'

team_dict = {
    'arsenal': 'Arsenal',
    'aston villa': 'Aston Villa',
    'brentford': 'Brentford',
    'brighton': 'Brighton & Hove Albion',
    'burnley': 'Burnley',
    'chelsea': 'Chelsea',
    'crystal palace': 'Crystal Palace',
    'everton': 'Everton',
    'leeds united': 'Leeds United',
    'leicester city': 'Leicester City',
    'liverpool': 'Liverpool',
    'manchester city': 'Manchester City',
    'manchester united': 'Manchester United',
    'newcastle united': 'Newcastle United',
    'norwich city': 'Norwich City',
    'southampton': 'Southampton',
    'tottenham': 'Tottenham Hotspur',
    'watford': 'Watford',
    'west ham united': 'West Ham United',
    'wolverhampton': 'Wolverhampton Wanderers'
}

class V(Enum):
    interested = 0

class MacroGetInterested(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        interested = vars[V.interested.name][0]
        print("interested value:")
        print(interested)
        if interested == 'true':
            vars['INTERESTED'] = 'true'
            print('true')
        else:
            vars['INTERESTED'] = 'false'
            print('false')


class MacroHome(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        user_input = input().lower()
        if user_input in team_dict:
            team_name = team_dict[user_input]
            # make team_name into team id
            url = "https://sofascores.p.rapidapi.com/v1/teams/rankings"
            querystring = {"name": team_name}
            headers = {
                "X-RapidAPI-Key": "dbad2f5186msh2f81b29abdc6d29p17a232jsndd11cefd33a8",
                "X-RapidAPI-Host": "sofascores.p.rapidapi.com"
            }
            response = requests.request("GET", url, headers=headers, params=querystring)
            data = response.json()['data']
            ranking = data[0]['ranking']
            year = data[0]['year']
            vars['home_team_ranking'] = ranking
            # [team name] ranked [rank] in [2021]
            print(team_name + " is ranked #" + str(ranking) + " in " + str(year))
        else:
            print('That team is not part of EPL')


transitions = {
        'state': 'start',
        '`Hi, I am dEPLoyer! Have you ever heard of Manchester United? `': {
            '[yes]': 'familiar',
            '[no]': 'unfamiliar',
        },
    }

familiar = {
        'state': 'familiar',
        '`Do you watch EPL in your free time?`': {
            '[yes]': {
                '`I do too! Do you have a favorite team?`': {
                    '#GET_HOME_TEAM': 'end'
                    },
                    '[no]': {
                        '`okay`': 'end'
                    },
                }
            },

            '[no]': {
                '`Why do you not watch it?`': {
                    '[not interested]': {
                        '`I love EPL for xxxxxxx, does this interest you?` ': {
                            '[yes]': 'end'
                        }
                    },
                    '[dont know]': 'introducing EPL'
                }
            },
        }


unfamiliar={
    'state':'unfamiliar',
    '`Manchester United is part of EPL.  The Premier League was founded in 1992, '
    'replacing the First Division as the top tier of English football. Does this sound interesting to you?`':{
        '[yes]':{
            '`Great! Manchester United is one of the most successful teams in the English Premier League. The famous player'
            'Cristiano Ronaldo was once a member of Manchester United!`':{
                '#SET_INTERESTED #GET_INTERESTED':{
                    '#IF($INTERESTED=true) `Manchester United can be one of my favorite team. Do you have any favorite team in EPL so far?`':{
                        '[yes]':{
                            '`Good for you! `':'match_discussion'
                        },
                        'error':{
                        '`Oh that\'s fine. I watched Manchester United\'s recent game with Sevilla, another team in EPL. It was so intense! They got 2-2 eventually.`':{
                                '#SET_INTERESTED #GET_INTERESTED':{
                                    '#IF($INTERESTED=true) `I know! Sabitzer from Manchester United had the first goal 14 minutes after the game for his team! '
                                    'That is such a quick goal! Given that the average first goal for soccer game is after 30 minutes on average!`':{
                                        '#SET_INTERESTED #GET_INTERESTED':{
                                            '#IF($INTERESTED=true)`Manchester United’s squad is one of the biggest in the Premier League and it’s filled up with quality players in every position. '
                                                  'They are actually gonna have a game with Tottenham Hotspur soon.'
                                                 'They have long been rivals with each other and Hotspur currently ranks one below Manchester United!'
                                                 'Do you bother betting on their results?`':{
                                                     '#UNX':{
                                                         '` I would say 2-0. It somehow made me recall their game last year in October. They had 0-0 at half time.`':'end'
                                                     },
                                                 },
                                            },
                                            '#IF($INTERESTED=false)':'fun_fact'
                                        }

                                    }
                                }
                                    },
                                      '#IF($INTERESTED=false)':'fun_fact'
                           }
                        },
                    '#IF($INTERESTED=false)':'fun_fact'
                    }
                }
            },
        '`[no]`':'player_recommendation'

    }



player_recommendation={
    'state':'player_recommendation',
    '#GATE `Do you want to know more about some players? Marcus Rashford is my favorite from Manchester United. Well, if you\'re looking for a football player who can run faster than a cheetah on Red Bull, score goals like it\'s his job (oh wait,'
    'it actually is his job), and make the opposing team\'s defense look like a bunch of lost toddlers, then Marcus Rashford is your man. `':'rashford_rec',
    '#GATE `Do you want to know more about some players? Harry Kane is my favorite from Tottenham Hotspur. He is not '
    'just a goal-scoring machine, he\'s also a great team player.'
    ' He has a knack for creating chances for his teammates and can change the course of a game with his passing and playmaking abilities.`':'kane_rec',
}

rashford_rec={
    'state':'rashford_rec',
    '`In fact, if football was a video game, Marcus would be the cheat code that everyone wants to unlock. `':{
        '#SET_INTERESTED #GET_Interested':{
            '#IF($INTERESTED=true)':{
                '`Rashford appeared 233 times in this season and had 74 goals. He is absolutely one of the heated players. Do you want to look at some of his game stats?`:{'
                '[yes]':{
                    '`stats Speaking of this, I am a big fan of Manchester United as well. Do you think you would like Manchester United? Manchester United is a team with a rich history and a tradition of excellence.'
                    'If you want to support a team that has consistently been among the best in the world, then Manchester United is a great choice.`':{
                        '[yes]':{
                            '`cool`':'end'
                        },
                        '[no]':'team_recommendation'
                    }
                },
                '[no]':'player_recommendation'
            },
            '#IF($INTERESTED=false)':'player_recommendation'
        }
    }
}
kane_rec={
    'state':'kane_rec',
    '`Despite his success on the field, Harry Kane remains humble and grounded.`':{
         '#GET_Interested':{
            '#IF($INTERESTED=true)':{
                '`Harry Kane appeared 313 times in this season and had 206 goals. You can call him one of the most successful commissioned players. Do you want to know how he performed?`':{
                '[yes]':{
                    '`stats Tottenham Hotspur is viral these days! Some of their players made wonderful performance at the World Cup.'
                    'I personally like this team a lot! Do you think you would like it?`':{
                        '[yes]':{
                            'cool':'end'
                        },
                        '[no]':'team_recommendation'
                    }
                },
               '[no]':'player_recommendation'
                }
        },
            '#IF($INTERESTED=false)':'player_recommendation'
         }
    }
}

team_recommendation={
    'state':'team_recommendation',
    '`say teams`':'end'
}

macros = {
        'GET_HOME_TEAM': MacroHome(),
        'SET_INTERESTED': MacroGPTJSON(
            'Do you think the user is interested in knowing more?',
            {V.interested.name: ["true","false"]}
        ),
        'GET_INTERESTED': MacroGetInterested()
    }



df = DialogueFlow('start', end_state='end')
df.load_transitions(transitions)
df.load_transitions(familiar)
df.load_transitions(unfamiliar)
df.load_transitions(player_recommendation)
df.load_transitions(rashford_rec)
df.load_transitions(kane_rec)
df.load_transitions(team_recommendation)
df.add_macros(macros)

if __name__ == '__main__':
    openai.api_key_path = utils.OPENAI_API_KEY_PATH
    df.run()