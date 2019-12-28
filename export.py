import pymongo
import json
from langdetect import detect
from scrapy.utils.project import get_project_settings
from collections import Counter
import sys
from functools import reduce
from copy import deepcopy,copy
from collections import defaultdict
from tqdm import tqdm
import spacy
from spacymoji import Emoji
import re
def checkDualReply(context,i):
    checkReply = lambda tweet:tweet['is_reply']   #and len(tweet['reply_to']) == 2
    checkDual = lambda first,last:  first['user_id'] in  last['reply_to'] #last['reply_to'][-1] == first['user_id']
    first,last = context[i-1],context[i]
    if checkReply(last): #and checkReply(first):
        return checkDual(first,last) and first['user_id'] != last['user_id']
    else:
        return False
def squeezeContext(context):
    out = []
    for tweet in context:
        if out == []:
            out.append([tweet])
        elif out[-1][-1]['user_id'] == tweet['user_id']:
            out[-1].append(tweet)
        else :
            out.append([tweet])
    
    return out
        

def check(context,start_index=3):
    for i,tweet in enumerate(reversed(context[start_index:])):
        if tweet['emoji'] :
            index = len(context)-i-1 
            #return squeezeContext(context[:index+1])
            if checkDualReply(context,i):
                return context[:index+1]


def loadConversa(conversas):

    outs = []
    users = []
    for conversa  in conversas:
        context = conversa['context']
        tweets = check(context,1)
        if tweets:
            users.append(tweets[-1]['usernameTweet'])
            outs.append(tweets)
    userCount = Counter(users)
    return outs,users,userCount


def build_tree(outs,ids):
    treeDict = {}
    nodes = {tweet['ID']:{'content':tweet,'next':dict()}  for i in ids for tweet in outs[i]}
    # add pre and next
    for i in ids:
        for index,tweet in enumerate(outs[i]):
            if index<len(outs[i])-1: 
                ID = outs[i][index+1]['ID']
                nodes[tweet['ID']]['next'][ID]  = nodes[ID]
            if index>0: nodes[tweet['ID']]['prev'] = nodes[outs[i][index-1]['ID']]
    #get root
    get_prev = lambda node: get_prev(node['prev']) if node.get('prev') else node['content']['ID']
    roots = set([get_prev(nodes[outs[i][0]['ID']]) for i in ids]) 
    return {i:nodes[i] for i in roots}

def flat(node):
    keys = [k for k in node.keys() if k!='content']
    if len(keys)>0:
        for kk in keys:
            yield from flat(node[kk])
    else:
        yield node


def splitTreeIndex(outs):
    ids = [[ii['ID'] for ii in i] for i in outs]
    idDict = defaultdict(list)
    for index,i in enumerate(ids):
        for ii in i:
            idDict[ii].append(index)


    tree = set([ii for i in list(idDict.values()) if len(i)!=1 for ii in i])
    other = [i for i in range(len(outs)) if i not in tree]
    return tree,other
        

def tree2list(node,out):
    keys = list(node['next'].keys())
    out.append(node['content'])
    if len(keys)==1:
        yield from tree2list(node['next'][keys[0]],out)
    elif len(keys) > 1:
        for kk in keys:
            yield from tree2list(node['next'][kk],copy(out))
    else:
        yield out

def build_data(dataset):

    outs,users,userCount = loadConversa(dataset) 
    print(len(outs))
    treeIndex,otherIndex =  splitTreeIndex(outs)
    treeData=build_tree(outs,treeIndex)
    treelist = [list(tree2list(v,[])) for k,v in treeData.items()]
    allData = treelist + [[outs[i]] for i in otherIndex]
    return allData
def writeData(dataset,callback=lambda x: True):
    with open('./output','wt') as f:
        for i in filter(callback,dataset):
            print(json.dumps(i[0],ensure_ascii= False),file=f)
def read_data(file_name):
    for line in tqdm(open(file_name)):
        yield json.loads(line)
if __name__ == "__main__":
    SETTINGS = get_project_settings()
    if sys.argv[-1]  == 'db':
        connection = pymongo.MongoClient(SETTINGS['MONGODB_SERVER'], SETTINGS['MONGODB_PORT'])
        db = connection[SETTINGS['MONGODB_DB']]
        conversaCollection = db[SETTINGS['MONGODB_CONVERSA_COLLECTION']]
        conversas = conversaCollection.find().sort('_id',pymongo.ASCENDING).limit(100000)
    else:
        pass 
    #first is reply and len is not 11(ancestors 10 + 1) may reply_to is deleted 
    #so it may cause bug in crawl,need use try except and mark coversion done
    #needMoreContext = [i for i in  read_data(SETTINGS['SAVE_CONVERSA_FILE'])  if i['context'][0]['is_reply'] and len(i['context'])==11]
    #noMoreContext = [i for i in read_data(SETTINGS['SAVE_CONVERSA_FILE'])  if i['context'][0]['is_reply'] and len(i['context'])<11]
    #other = filter(lambda i:not (i['context'][0]['is_reply'] and len(i['context'])==11),read_data(SETTINGS['SAVE_CONVERSA_FILE']))
    #other = filter(lambda i: not i['context'][0]['is_reply'],read_data(SETTINGS['SAVE_CONVERSA_FILE']))
    #多了1/4
    other = filter(lambda i:True,read_data(SETTINGS['SAVE_CONVERSA_FILE']))
    #filter first one is reply. if need more data,I will add that one  to crawl. about  1/4  outs.
    #because there are bug in build tree,tree is not true 
    '''outs,users,userCount = loadConversa(other) 
    treeData=build_tree(outs)
    list_of_list = [list(tree2list(v,[])) for k,v in treeData.items()]
    x,_,_=loadConversa(x)'''
    
    #needMore = build_data(needMoreContext)
    writeData(build_data(other),callback = lambda x: len(x)==1)
    '''print('\n\n\n')
    nlp = spacy.load('en')
    emoji = Emoji(nlp)
    nlp.add_pipe(emoji, first=True)
    out = []
    for i in read_data(SETTINGS['SAVE_CONVERSA_FILE']):
        for ii in i['context']:
            if ii['emoji']:
                outStr = re.sub('[0-9*?#]','',ii['emoji'])
                if outStr:
                    if '\u200d' in outStr or '\ufe0f' in outStr  or '🏻' in outStr or '🏼' in outStr or  '🏽' in outStr or '🏾' in outStr or '🏿' in outStr or re.search("["u"\U000e0062-\U000e007f""]",outStr):
                        for xxxx in nlp(outStr)._.emoji:
                            out.append(xxxx[0])
                    else:
                        out.extend(list(outStr.replace(' ','')))
    xxx=Counter(out)
    #xx=sorted(xx,key=lambda x:x.encode('unicode_escape'))
    with open('emoji','w') as f:
        for i,num in xxx.most_common():
            print(i,num,sep='\t',file=f)'''