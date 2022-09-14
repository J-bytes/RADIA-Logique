import numpy as np
from functools import reduce
import os
import pandas as pd
import pymongo
import yaml
import urllib

class MongoDB:
    def __init__(self, address, port, collectionnames):
        #assert urllib.request.urlopen(f"{address}:{port}").getcode() == 200 #make sure connection is up

        self.client = pymongo.MongoClient(address, port)
        self.db_public = self.client["Public_Images"]
        for collectionname in collectionnames:
            assert collectionname in self.db_public.list_collection_names()
        self.db_CIUSSS = self.client["CIUSSS"]

        self.data = [self.db_CIUSSS["images"]]

        with open("data/data.yaml", "r") as stream:
            columns = yaml.safe_load(stream)["names"]

        # columns.remove("Age")# TODO : Fix this
        #columns.remove("Lung Opacity")
        #columns.remove("Pleural Other")
        # columns.remove("Enlarged Cardiomediastinum")
        #columns.remove("Pleural Thickening")
        self.names = columns

        for name in collectionnames:
            self.data.append(self.db_public[name])


    def dataset(self, datasetname, classnames):
        assert datasetname == "Train" or datasetname == "Valid"
        train_dataset = []


        query = {datasetname: 1,"Frontal/Lateral": "F"}

        if len(classnames) > 0:
            query["$or"] = [{classname: {"$in" : [1,-1]}} for classname in classnames]

        for collection in self.data:
            results = list(collection.find(query))
            print(f"Collected query for dataset {collection}")

            if len(results) > 0:
                columns = results[0].keys()
                data=pd.DataFrame(results, columns=columns)
                print(data.columns)
                #data = data[self.names + ["Path"]]
                data["collection"] = collection.name
                #data[self.names] = data[self.names].astype(np.int32)
                train_dataset.append(data)

        if len(train_dataset) > 1:

            # columns = list(columns)
            # columns.remove("AP/PA")

            df = pd.concat(train_dataset, join='outer')
        elif len(train_dataset) == 1:
            df = train_dataset[0]
        else:
            raise Exception("No data found")


        #set up parent class
        print(df.columns)
        df["Opacity"] = df[["Consolidation","Atelectasis","Mass","Nodule","Lung Lesion","Lung Opacity"]].replace(-1,1).max(axis=0)
        df["Air"]     = df[["Emphysema","Pneumothorax","Pneumo other"]].replace(-1,1).max(axis=0)
        df["Liquid"]  = df[["Edema","Pleural Effusion"]].replace(-1, 1).max(axis=0)
        columns = self.names + ["Path", "collection"]
        df.fillna(0, inplace=True)
        return df[columns]


if __name__ == "__main__":
    import yaml

    os.environ["DEBUG"] = "False"
    with open("data/data.yaml", "r") as stream:
        names = yaml.safe_load(stream)["names"]

    # db = MongoDB("10.128.107.212", 27017, ["ChexPert", "ChexNet", "ChexXRay"])

    db = MongoDB("10.128.107.212", 27017, ["ChexPert", "ChexNet","ChexPad"])
    print("database initialized")
    train = db.dataset("Train", [])
    print("training dataset loaded")
    valid = db.dataset("Valid", [])
    print("validation dataset loaded")
    valid.iloc[0:100].to_csv("valid.csv")
    # valid = valid[names]
    print(valid.head(100))
