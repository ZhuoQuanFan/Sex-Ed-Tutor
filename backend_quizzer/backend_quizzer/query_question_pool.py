from scipy.stats import wasserstein_distance
import numpy as np
from pyemd import emd_with_flow
import math

from elasticsearch import Elasticsearch
import random

es = Elasticsearch('http://localhost:9200')


def search_question(keyword, cluster = '', post_id = 'none', type = 'design_element', search_size=100):
    # Input:
    # Return:
    rand_index = random.randint(1, 100)
    if type == 'design_element':
        if post_id == 'none':
            if cluster != '':
                if keyword != '':
                    if rand_index < 70:
                        dsl = {
                            'query': {
                                'match': {
                                    'right_answer': keyword
                                }
                            }
                        }
                    else:
                        if cluster != 'color_design':
                            dsl = {
                                'query': {
                                    'match': {
                                        'answer_cluster': cluster
                                    }
                                }
                            }
                        else:
                            dsl = {
                                'query': {
                                    "bool": {
                                        "should": [
                                            {"match": {"answer_cluster": "color_design"}},
                                            {"match": {"answer_cluster": "visual_design"}}
                                        ]
                                    }
                                }
                            }
                else:
                    if cluster != 'color_design':
                        dsl = {
                            'query': {
                                'match': {
                                    'answer_cluster': cluster
                                }
                            }
                        }
                    else:
                        # Enter here.
                        dsl = {
                            'query': {
                                "bool": {
                                    "should": [
                                        {"match": {"answer_cluster": "color_design"}},
                                        {"match": {"answer_cluster": "visual_design"}}
                                    ]
                                }
                            }
                        }

            else:
                if keyword != '':
                    if rand_index < 70:
                        dsl = {
                            'query': {
                                'match': {
                                    'right_answer': keyword
                                }
                            }
                        }
                    else:
                        search_size = 780
                        dsl = {
                            'query': {
                                'match_all': {}
                            }
                        }
                else:
                    search_size = 780
                    dsl = {
                        'query': {
                            'match_all': {}
                        }
                    }

        else:
            if cluster != '':
                if keyword != '':
                    if rand_index < 70:
                        if cluster != 'color_design':
                            dsl = {
                                'query': {
                                    "bool": {
                                        "must": [
                                            {
                                                "match": {
                                                    'post_id': post_id
                                                }
                                            },
                                            {
                                                "match": {
                                                    'answer_cluster': cluster
                                                }
                                            },
                                            {
                                                'match': {
                                                    'right_answer': keyword
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        else:
                            dsl = {
                                'query': {
                                    "bool": {
                                        "must": [
                                            {
                                                "match": {
                                                    'post_id': post_id
                                                }
                                            },
                                            {
                                                "bool": {
                                                    "should": [
                                                        {"match": {"answer_cluster": "color_design"}},
                                                        {"match": {"answer_cluster": "visual_design"}}
                                                    ]
                                                }
                                            },
                                            {
                                                'match': {
                                                    'right_answer': keyword
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                    else:
                        if cluster != 'color_design':
                            dsl = {
                                'query': {
                                    'match': {
                                        'answer_cluster': cluster
                                    }
                                }
                            }
                        else:
                            dsl = {
                                'query': {
                                    "bool": {
                                        "should": [
                                            {"match": {"answer_cluster": "color_design"}},
                                            {"match": {"answer_cluster": "visual_design"}}
                                        ]
                                    }
                                }
                            }
                else:
                    search_size = 780
                    if cluster != 'color_design':
                        dsl = {
                            'query': {
                                "bool": {
                                        "must": [
                                            {
                                                "match": {
                                                    'post_id': post_id
                                                }
                                            },
                                            {
                                                "match": {
                                                    'answer_cluster': cluster
                                                }
                                            }
                                        ]
                                    }
                            }
                        }
                    else:
                        dsl = {
                            'query': {
                                "bool": {
                                    "must": [
                                        {
                                            "match": {
                                                'post_id': post_id
                                            }
                                        },
                                        {
                                            "bool": {
                                                "should": [
                                                    {"match": {"answer_cluster": "color_design"}},
                                                    {"match": {"answer_cluster": "visual_design"}}
                                                ]
                                            }
                                        }
                                    ]
                                }
                            }
                        }
            else:
                dsl = {
                    'query': {
                        'match': {
                            'post_id': post_id
                        }
                    }
                }
    else:
        if cluster == '':
            if keyword != '':
                print(keyword)
                dsl = {
                    'query': {
                        'match': {
                            'ui_elements': keyword
                        }
                    }
                }
            else:
                search_size = 780
                dsl = {
                    'query': {
                        'match_all': {}
                    }
                }
        else:
            if keyword != '':
                if cluster != 'color_design':
                    dsl = {
                        'query': {
                            "bool": {
                                "must": [
                                    {
                                        "match": {
                                            'answer_cluster': cluster
                                        }
                                    },
                                    {
                                        'match': {
                                            'right_answer': keyword
                                        }
                                    }
                                ]
                            }
                        }
                    }
                else:
                    dsl = {
                        'query': {
                            "bool": {
                                "must": [
                                    {
                                        "bool": {
                                            "should": [
                                                {"match": {"answer_cluster": "color_design"}},
                                                {"match": {"answer_cluster": "visual_design"}}
                                            ]
                                        }
                                    },
                                    {
                                        'match': {
                                            'right_answer': keyword
                                        }
                                    }
                                ]
                            }
                        }
                    }
            else:
                if cluster != 'color_design':
                    dsl = {
                        'query': {
                            'match': {
                                'answer_cluster': cluster
                            }
                        }
                    }
                else:
                    dsl = {
                        'query': {
                            "bool": {
                                "should": [
                                    {"match": {"answer_cluster": "color_design"}},
                                    {"match": {"answer_cluster": "visual_design"}}
                                ]
                            }
                        }
                    }
    # dsl = {
    #     'query': {
    #         'match_all': {
    #         }
    #     }
    # }
    result = es.search(index='question_pool_all', size=search_size, body=dsl)
    result_list = result['hits']['hits']
    return_results = []
    for i in range(len(result_list)):
        # print(result_list[i]['_source'])
        # print(result_list[i]['_source']['question'])
        # print(result_list[i]['_source']['right_answer'])
        # print(result_list[i]['_source']['mention_ui_elements'])
        # print(result_list[i]['_source']['other_options_wiki'])
        return_results.append(result_list[i]['_source'])
    print(len(return_results))
    return return_results

print('haaha')
# search_question('black')#, type = 'ui_element')

