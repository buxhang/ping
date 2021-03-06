# -*- coding:utf8 -*-
import os
import csv
import numpy as np
import pandas as pd
from sklearn import preprocessing
import lightgbm as lgb
from sklearn.model_selection import train_test_split


path_train = "/data/dm/train.csv"  # 训练文件
path_test = "/data/dm/test.csv"  # 测试文件

path_test_out = "model/"  # 预测结果输出路径为model/xx.csv,有且只能有一个文件并且是CSV格式。


def data_process_train(path_train):
    #print('Load data......')
    train_data = pd.read_csv(path_train)

    #训练数据处理
    """时间特征处理，抽出了星期，月份，小时，但是还没有做哑编码（one-hot）!!!!!!!"""
    # 把数据加上星期，月份，小时这三个空列，后面再补内容
    train_columns = list(train_data.columns)  # 获取列名
    train_columns.append("weekday")
    train_columns.append("month")
    train_columns.append("hour")
    train_data.reindex(columns=train_columns)  # 为了添加星期，月份，小时这三个特征
    # print(train_columns)

    # 时间处理
    # Unix时间戳，1476923580这样子的，转成2016-10-20 08:33:00这样子的
    train_data["TIME"] = pd.to_datetime(train_data["TIME"], unit='s')  # 把unix时间转成人能看明白的，单位到秒（s）
    # 这个dt太方便了，要啥取啥就行
    train_data["weekday"] = train_data["TIME"].dt.weekday  # 星期，The day of the week with Monday=0, Sunday=6
    train_data["month"] = train_data["TIME"].dt.month
    train_data["hour"] = train_data["TIME"].dt.hour

    # print (train_data)
    # print (train_data["TIME"].dt.weekday)
    # print (train_data["TIME"].dt.month)
    # print (train_data["TIME"].dt.hour)

    # 方向信息缺失值处理
    train_data["DIRECTION"].replace(-1, np.nan, inplace=True)  # inplace就是直接在train_data上改了，train_data就会变，不用再赋值回去了
    train_data["DIRECTION"].replace(np.nan, train_data["DIRECTION"].mean(0),
                                    inplace=True)  # 先把-1换成nan，然后求平均数的时候就不会带上这个nan了。然后再把缺失值换成能记录到的角度的平均数
    # 或者上面这一行代码和下面这一堆的代码效果是一样的......
    # imp = preprocessing.Imputer(missing_values='NaN',strategy='mean',axis=0,copy=False)
    # imp.fit(train_data["DIRECTION"].reshape((-1,1)))
    # imp.transform(train_data["DIRECTION"].reshape((-1,1)))
    # print (train_data.loc[0:60,"DIRECTION"])

    # 方向，高度，速度，都做归一化，不做z-score标准化，我感觉，这些数据不像是服从正态分布的（如果服从正态分布的，就用z-score了）
    # 其实非常简单，就是个缩放
    min_max_scaler = preprocessing.MinMaxScaler()
    train_data[["DIRECTION", "HEIGHT", "SPEED"]] = min_max_scaler.fit_transform(
        train_data[["DIRECTION", "HEIGHT", "SPEED"]])
    # print (train_data[["DIRECTION","HEIGHT","SPEED"]])


    # weekday，month，hour，callstate做哑编码(one-hot)。直接用concat把这些新列加进来
    train_data = pd.concat([train_data, pd.get_dummies(train_data["weekday"], prefix='weekday')], axis=1)
    train_data = pd.concat([train_data, pd.get_dummies(train_data["month"], prefix='month')], axis=1)
    train_data = pd.concat([train_data, pd.get_dummies(train_data["hour"], prefix='hour')], axis=1)
    train_data = pd.concat([train_data, pd.get_dummies(train_data["CALLSTATE"], prefix='CALLSTATE')], axis=1)
    train_data.drop(['TERMINALNO', 'TIME', 'TRIP_ID', 'CALLSTATE', 'weekday', 'month', 'hour'], axis=1, inplace=True)

    # 把Y值挪到最后一列
    cols = list(train_data.columns)
    cols.insert(len(cols) - 1, cols.pop(cols.index('Y')))
    #print(cols)  # 这个是目前的特征和Y值
    # print (train_data.reindex(columns=cols))
    # 这个copy都不管用啊，只能这样了，可读性有点低
    train_data=train_data.reindex(columns=cols)
    return train_data

def data_process_test(path_test):
    test_data = pd.read_csv(path_test)

    # 训练数据处理
    """时间特征处理，抽出了星期，月份，小时，但是还没有做哑编码（one-hot）!!!!!!!"""
    # 把数据加上星期，月份，小时这三个空列，后面再补内容
    test_columns = list(test_data.columns)  # 获取列名
    test_columns.append("weekday")
    test_columns.append("month")
    test_columns.append("hour")
    test_data.reindex(columns=test_columns)  # 为了添加星期，月份，小时这三个特征
    # print(test_columns)

    # 时间处理
    # Unix时间戳，1476923580这样子的，转成2016-10-20 08:33:00这样子的
    test_data["TIME"] = pd.to_datetime(test_data["TIME"], unit='s')  # 把unix时间转成人能看明白的，单位到秒（s）
    # 这个dt太方便了，要啥取啥就行
    test_data["weekday"] = test_data["TIME"].dt.weekday  # 星期，The day of the week with Monday=0, Sunday=6
    test_data["month"] = test_data["TIME"].dt.month
    test_data["hour"] = test_data["TIME"].dt.hour

    # print (test_data)
    # print (test_data["TIME"].dt.weekday)
    # print (test_data["TIME"].dt.month)
    # print (test_data["TIME"].dt.hour)

    # 方向信息缺失值处理
    test_data["DIRECTION"].replace(-1, np.nan, inplace=True)  # inplace就是直接在test_data上改了，test_data就会变，不用再赋值回去了
    test_data["DIRECTION"].replace(np.nan, test_data["DIRECTION"].mean(0),
                                    inplace=True)  # 先把-1换成nan，然后求平均数的时候就不会带上这个nan了。然后再把缺失值换成能记录到的角度的平均数
    # 或者上面这一行代码和下面这一堆的代码效果是一样的......
    # imp = preprocessing.Imputer(missing_values='NaN',strategy='mean',axis=0,copy=False)
    # imp.fit(test_data["DIRECTION"].reshape((-1,1)))
    # imp.transform(test_data["DIRECTION"].reshape((-1,1)))
    # print (test_data.loc[0:60,"DIRECTION"])

    # 方向，高度，速度，都做归一化，不做z-score标准化，我感觉，这些数据不像是服从正态分布的（如果服从正态分布的，就用z-score了）
    # 其实非常简单，就是个缩放
    min_max_scaler = preprocessing.MinMaxScaler()
    test_data[["DIRECTION", "HEIGHT", "SPEED"]] = min_max_scaler.fit_transform(
        test_data[["DIRECTION", "HEIGHT", "SPEED"]])
    # print (test_data[["DIRECTION","HEIGHT","SPEED"]])


    # weekday，month，hour，callstate做哑编码(one-hot)。直接用concat把这些新列加进来
    test_data = pd.concat([test_data, pd.get_dummies(test_data["weekday"], prefix='weekday')], axis=1)
    test_data = pd.concat([test_data, pd.get_dummies(test_data["month"], prefix='month')], axis=1)
    test_data = pd.concat([test_data, pd.get_dummies(test_data["hour"], prefix='hour')], axis=1)
    test_data = pd.concat([test_data, pd.get_dummies(test_data["CALLSTATE"], prefix='CALLSTATE')], axis=1)
    test_data.drop(['TIME', 'TRIP_ID', 'CALLSTATE', 'weekday', 'month', 'hour'], axis=1, inplace=True)


    return test_data

def process():
    total_data=data_process_train(path_train)
    X_train, X_val, y_train, y_val = train_test_split(total_data.iloc[:, 0:-1], total_data.iloc[:, -1], test_size=0.2,
                                                      random_state=0)

    # print (X_train)
    # print (X_test)
    # print (y_train)
    # print (y_test)
    # create dataset for lightgbm
    lgb_train = lgb.Dataset(X_train, y_train)
    lgb_eval = lgb.Dataset(X_val, y_val, reference=lgb_train)

    # specify your configurations as a dict
    params = {
        'task': 'train',
        'boosting_type': 'gbdt',
        'objective': 'regression',
        'metric': {'l2', 'auc'},
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': 0
    }

    print('Start training...')
    # train
    gbm = lgb.train(params,
                    lgb_train,
                    num_boost_round=20,
                    valid_sets=lgb_eval,
                    early_stopping_rounds=5)

    # print('Save model...')
    # save model to file
    # gbm.save_model('model.txt')

    print('Start predicting...')
    # predict

    X_test=data_process_test(path_test)
    out=X_test["ERMINALNO"]
    X_test.drop(labels="ERMINALNO")
    y_pred = gbm.predict(X_test, num_iteration=gbm.best_iteration)
    out.reindex(columns=["ERMINALNO","y_pred"])
    out["y_pred"]=y_pred
    out.drop_duplicates('ERMINALNO',inplace=True)  #对ID去重
    out.to_csv(path_test_out+"result.csv",index=False,header=["Id","Pred"])







if __name__ == "__main__":
    print("****************** start **********************")
    # 程序入口
    process()
