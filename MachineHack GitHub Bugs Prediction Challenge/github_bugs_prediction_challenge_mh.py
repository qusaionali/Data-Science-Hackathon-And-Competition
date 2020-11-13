# -*- coding: utf-8 -*-
"""GitHub Bugs Prediction Challenge MH.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/19O9gpxcSsAC2KobTQspzGGS5fM1jtErn
"""

!wget https://machinehack-be.s3.amazonaws.com/predict_github_issues_embold_sponsored_hackathon/Embold_Participant%27s_Dataset.zip

ls

!unzip "Embold_Participant's_Dataset.zip"

# Commented out IPython magic to ensure Python compatibility.
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# %matplotlib inline
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# %matplotlib inline
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
!pip install rfpimp
!pip install catboost
from sklearn.metrics import mean_absolute_error,accuracy_score
import lightgbm as lgb
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import StratifiedKFold,KFold,GridSearchCV,GroupKFold,train_test_split,StratifiedShuffleSplit
from rfpimp import *
from tqdm import tqdm
from catboost import *
from sklearn.neighbors import KNeighborsClassifier
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from fastai.text import *
from fastai.imports import *
from fastai.text import *
from fastai import *
# %matplotlib inline

from sklearn.ensemble import *
from sklearn.model_selection import *
from sklearn.metrics import *
from catboost import CatBoostClassifier
import nltk
!pip install sentence-transformers
from sentence_transformers import SentenceTransformer

sns.set_style('darkgrid')
import os
from fastai.text import *
from fastai.imports import *
from fastai.text import *
from fastai import *

train=pd.read_json("/content/Embold_Participant's_Dataset/embold_train.json")
traine=pd.read_json("/content/Embold_Participant's_Dataset/embold_train_extra.json")
test=pd.read_json("/content/Embold_Participant's_Dataset/embold_test.json")
sub=pd.read_csv("/content/Embold_Participant's_Dataset/sample submission.csv")

train.head(5)

traine.head(5)

test.head(5)

sub.head(5)

train.isnull().sum(),traine.isnull().sum(),test.isnull().sum(),train.shape,traine.shape,test.shape,train.dtypes

train=train.append(traine,ignore_index=True)

train.head(5)

train.shape

train=train.sample(frac =.30)

"""# method-1 (fastai+bert)"""

train['text']=train['title']+' '+train['body']
test['text']=test['title']+' '+test['body']
del train['title']
del test['title']
del train['body']
del test['body']
train['target']=train['label']
del train['label']

train['target'].value_counts()

train.isnull().sum(),test.isnull().sum()

import re
def clean_text(text):
    text = text.lower()
    text = re.sub(r'@[a-zA-Z0-9_]+', '', text)   
    text = re.sub(r'https?://[A-Za-z0-9./]+', '', text)   
    text = re.sub(r'www.[^ ]+', '', text)  
    text = re.sub(r'[a-zA-Z0-9]*www[a-zA-Z0-9]*com[a-zA-Z0-9]*', '', text)  
    text = re.sub(r'[^a-zA-Z]', ' ', text)   
    text = [token for token in text.split() if len(token) > 2]
    text = ' '.join(text)
    return text

train['text'] = train['text'].apply(clean_text)
test['text'] = test['text'].apply(clean_text)

def random_seed(seed_value):
    import random 
    random.seed(seed_value)  
    import numpy as np
    np.random.seed(seed_value)  
    import torch
    torch.manual_seed(seed_value)  
    
    if torch.cuda.is_available(): 
        torch.cuda.manual_seed(seed_value)
        torch.cuda.manual_seed_all(seed_value)  
        torch.backends.cudnn.deterministic = True   
        torch.backends.cudnn.benchmark = False

path = Path("/content/")
path.ls()

from sklearn.metrics import accuracy_score 
y_pred_totcb = []
c=[]
from sklearn.model_selection import KFold, RepeatedKFold
fold = KFold(n_splits=2, shuffle=True, random_state=0)
i=1

for train_index, test_index in fold.split(train):
    
    train_df = train.iloc[train_index]
    valid_df = train.iloc[test_index]

    random_seed(42)
    
    data_lm = TextLMDataBunch.from_df(Path(path), train_df, valid_df, test, text_cols=[0], bs=32)
    data_clas = TextClasDataBunch.from_df(Path(path), train_df, valid_df, test, text_cols=[0], label_cols=1, bs=32)
    
    learn = language_model_learner(data_lm, AWD_LSTM, drop_mult=0.4, model_dir='/tmp/model/')
    learn.fit_one_cycle(1, 1e-2, moms=(0.8, 0.7))
    learn.unfreeze()
    learn.fit_one_cycle(1, 1e-3, moms=(0.8,0.7))
    learn.save_encoder('model_enc')
    
    learn = text_classifier_learner(data_clas, AWD_LSTM, drop_mult=0.4, model_dir='/tmp/model/')
    learn.load_encoder('model_enc')
    learn.fit_one_cycle(1, 1e-2, moms=(0.8, 0.7))
    learn.freeze_to(-2)
    learn.fit_one_cycle(1, slice(1e-2/(2.6**4),1e-2), moms=(0.8,0.7))
    learn.freeze_to(-1)
    learn.fit_one_cycle(1, slice(5e-3/(2.6**4),5e-3), moms=(0.8,0.7))
    learn.unfreeze()
    learn.fit_one_cycle(2, slice(1e-3/(2.6**4),1e-3), moms=(0.8,0.7))
   
    log_preds, test_labels = learn.get_preds(ds_type=DatasetType.Test, ordered=True)
    preds = np.argmax(log_preds, 1)
    c.append(log_preds)
    y_pred_totcb.append(preds)
    print(f'fold {i} completed')
    i = i+1

df = pd.DataFrame()
for i in range(1):
    col_name = 'SECTION_' + str(i)
    df[col_name] =  y_pred_totcb[i]

df.tail()

sub = pd.DataFrame()
sub['label'] = df.mode(axis=1)[0]
sub.tail()

m=[]
for i in range(30000):
  xx=df['SECTION_0'][i]
  yy=df['SECTION_1'][i]
  zz=min(xx,yy)
  m.append(zz)

sub['label']=

sub.to_csv('bertcz.csv',index=False)

"""# S mode"""

df = pd.concat([train, test]).reset_index()

df=train.append(test,ignore_index=True)

df.nunique(),df.shape

import string
punctuation=string.punctuation
df['title_umerics'] = df['title'].apply(lambda x: len([x for x in x.split() if x.isdigit()]))
df['title_upper'] = df['title'].apply(lambda x: len([x for x in x.split() if x.isupper()]))
df['title_punctuation_count'] = df['title'].apply(lambda x: len("".join(_ for _ in x if _ in punctuation)))

import string
punctuation=string.punctuation
df['body_umerics'] = df['body'].apply(lambda x: len([x for x in x.split() if x.isdigit()]))
df['body_upper'] = df['body'].apply(lambda x: len([x for x in x.split() if x.isupper()]))
df['body_punctuation_count'] = df['body'].apply(lambda x: len("".join(_ for _ in x if _ in punctuation)))

import re
def clean_text(text):
    text = text.lower()
    text = re.sub(r'@[a-zA-Z0-9_]+', '', text)   
    text = re.sub(r'https?://[A-Za-z0-9./]+', '', text)   
    text = re.sub(r'www.[^ ]+', '', text)  
    text = re.sub(r'[a-zA-Z0-9]*www[a-zA-Z0-9]*com[a-zA-Z0-9]*', '', text)  
    text = re.sub(r'[^a-zA-Z]', ' ', text)   
    text = [token for token in text.split() if len(token) > 2]
    text = ' '.join(text)
    return text

df['title'] = df['title'].apply(clean_text)
df['body'] = df['body'].apply(clean_text)

import nltk
nltk.download('stopwords')

import string
punctuation=string.punctuation
df['title_word_count']=df['title'].apply(lambda x: len(str(x).split(" ")))
df['title_char_count'] = df['title'].str.len()
def avg_word(sentence):
    words = sentence.split()
    return (sum(len(word) for word in words)/1+len(words))

df['title_avg_word'] = df['title'].apply(lambda x: avg_word(x))
from nltk.corpus import stopwords
stop = stopwords.words('english')

df['title_stopwords'] = df['title'].apply(lambda x: len([x for x in x.split() if x in stop]))
df['title_numerics'] = df['title'].apply(lambda x: len([x for x in x.split() if x.isdigit()]))
df['title_upper'] = df['title'].apply(lambda x: len([x for x in x.split() if x.isupper()]))
df['title_word_density'] = df['title_char_count'] / (df['title_word_count']+1)
df['title_punctuation_count'] = df['title'].apply(lambda x: len("".join(_ for _ in x if _ in punctuation)))

import string
punctuation=string.punctuation
df['body_word_count']=df['body'].apply(lambda x: len(str(x).split(" ")))
df['body_char_count'] = df['body'].str.len()
def avg_word(sentence):
    words = sentence.split()
    return (sum(len(word) for word in words)/1+len(words))

df['body_avg_word'] = df['body'].apply(lambda x: avg_word(x))
from nltk.corpus import stopwords
stop = stopwords.words('english')

df['body_stopwords'] = df['body'].apply(lambda x: len([x for x in x.split() if x in stop]))
df['body_numerics'] = df['body'].apply(lambda x: len([x for x in x.split() if x.isdigit()]))
df['body_upper'] = df['body'].apply(lambda x: len([x for x in x.split() if x.isupper()]))
df['body_word_density'] = df['body_char_count'] / (df['body_word_count']+1)
df['body_punctuation_count'] = df['body'].apply(lambda x: len("".join(_ for _ in x if _ in punctuation)))

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from nltk.tokenize import TreebankWordTokenizer
cvec = TfidfVectorizer(max_features=350, norm = 'l1', lowercase=True, smooth_idf=False, sublinear_tf=False, ngram_range=(1,4), tokenizer=TreebankWordTokenizer().tokenize)
df_info = pd.DataFrame(cvec.fit_transform(df['title']).todense())
df_info.columns = ['title_Top_' + str(c) for c in df_info.columns]
df = pd.concat([df, df_info], axis=1)

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from nltk.tokenize import TreebankWordTokenizer
cvec = TfidfVectorizer(max_features=100, norm = 'l1', lowercase=True, smooth_idf=False, sublinear_tf=False, ngram_range=(1,4), tokenizer=TreebankWordTokenizer().tokenize)
df_info = pd.DataFrame(cvec.fit_transform(df['body']).todense())
df_info.columns = ['body_Top_' + str(c) for c in df_info.columns]
df = pd.concat([df, df_info], axis=1)

from textblob import TextBlob
df['title_polarity'] = df.apply(lambda x: TextBlob(x['title']).sentiment.polarity, axis=1)
df['title_subjectivity'] = df.apply(lambda x: TextBlob(x['title']).sentiment.subjectivity, axis=1)

from textblob import TextBlob
df['body_polarity'] = df.apply(lambda x: TextBlob(x['body']).sentiment.polarity, axis=1)
df['body_subjectivity'] = df.apply(lambda x: TextBlob(x['body']).sentiment.subjectivity, axis=1)

j=[]
for i in df['title']:
  j.append(len(i))
df['title_len']=j
j=[]
for i in df['body']:
  j.append(len(i))
df['body_len']=j

del df['title']
del df['body']
train = df[df['label'].isnull()==False]
test = df[df['label'].isnull()==True]
del test['label']

train_df = df[df.label.notnull()]
test_df = df[df.label.isnull()]

X, y = train_df.drop(['label'], axis=1), train_df.label

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.10, random_state=42)

model_cat = CatBoostClassifier(depth=10,od_type='Iter', iterations=10000, task_type='GPU',eval_metric='Accuracy',bootstrap_type='Bayesian',od_wait=1000)
model_cat.fit(X_train, y_train.astype(int),
              eval_set=(X_test, y_test.astype(int)),
              early_stopping_rounds=200,
)

prediction = model_cat.predict(test_df[X_train.columns])
submission = pd.DataFrame(prediction, columns=['label'])
submission.to_csv('nowed.csv', index=False)
submission

"""# Roberta"""

!pip install simpletransformers

sample_sub =pd.read_csv("/content/Embold_Participant's_Dataset/sample submission.csv")

target = sample_sub.columns.tolist()

import numpy as np
import pandas as pd
from sklearn.metrics import *
from sklearn.model_selection import *

from tqdm import tqdm
import warnings
warnings.simplefilter('ignore')
import gc
from scipy.special import softmax

from simpletransformers.classification.classification_model import ClassificationModel
from sklearn.metrics import mean_squared_error as mse

train.head(2)

test.head(2)

def get_model(model_type, model_name, n_epochs = 2, train_batch_size = 112, eval_batch_size = 144, seq_len = 134, lr = 2e-5):
  model = ClassificationModel(model_type, model_name,num_labels=1, args={'train_batch_size':train_batch_size,
                                                                         "eval_batch_size": eval_batch_size,
                                                                         'reprocess_input_data': True,
                                                                         'overwrite_output_dir': True,
                                                                         'fp16': False,
                                                                         'do_lower_case': False,
                                                                         'num_train_epochs': n_epochs,
                                                                         'max_seq_length': seq_len,
                                                                         'regression': True,
                                                                         'manual_seed': 2,
                                                                         "learning_rate":lr,
                                                                         "save_eval_checkpoints": False,
                                                                         "save_model_every_epoch": False,})
  return model

tmp = pd.DataFrame()
tmp['text'] = train['text']
tmp['labels'] = train['target']
tmp_test = test[['text']].rename({'text': 'text'}, axis=1)
tmp_test['labels'] = 0
tmp_trn, tmp_val = train_test_split(tmp, test_size=0.15, random_state=2)

model = get_model('roberta', 'roberta-base', n_epochs=3)
import torch
torch.cuda.empty_cache()
model.train_model(tmp_trn)
import torch
torch.cuda.empty_cache()
preds_val = model.eval_model(tmp_val)[1]
preds_val = np.clip(preds_val, 0, 2)
print(f"RMSE: {mse(tmp_val['labels'], preds_val)**0.5}")
test_preds = model.eval_model(tmp_test)[1]
test_preds = np.clip(test_preds, 0, 2)
pv_1 = preds_val
pt_1 = test_preds

!nvidia-smi



data = (TextList.from_df(train, cols='text')
                .split_by_rand_pct(0.2)
                .label_for_lm()  
                .databunch(bs=48))
data.show_batch()

learn = language_model_learner(data, AWD_LSTM, drop_mult=0.3)

learn.fit_one_cycle(4)

learn.save('stage-1')

learn.unfreeze()

learn.load('stage-1')

learn.lr_find()

learn.recorder.plot()

data_clas = (TextList.from_df(train, cols='text', vocab=data.vocab)
             .split_by_rand_pct(0.2)
             .label_from_df(cols='target')
             .add_test(test)
             .databunch(bs=32))

data_clas.show_batch()

learn_classifier = text_classifier_learner(data_clas, AWD_LSTM, drop_mult=0.3)

learn_classifier.lr_find()

learn_classifier.recorder.plot()

learn_classifier.fit_one_cycle(1, 2e-2, moms=(0.8, 0.7))

