import os

import torch

from CheXpert2.dataloaders.CXRLoader import CXRLoader


# -------- proxy config ---------------------------

# proxy = urllib.request.ProxyHandler(
#     {
#         "https": "http://ccsmtl.proxy.mtl.rtss.qc.ca:8080",
#         "http": "http://ccsmtl.proxy.mtl.rtss.qc.ca:8080",
#     }
# )
# os.environ["HTTPS_PROXY"] = "http://ccsmtl.proxy.mtl.rtss.qc.ca:8080"
# os.environ["HTTP_PROXY"] = "http://ccsmtl.proxy.mtl.rtss.qc.ca:8080"
# # construct a new opener using your proxy settings
# opener = urllib.request.build_opener(proxy)
# # install the openen on the module-level
# urllib.request.install_opener(opener)



def test_dataloader_get_item():
    os.environ["DEBUG"] = "True"
    train = CXRLoader("Train", img_dir="", img_size=224)
    image, label = train[4]
    assert image.shape == (1, int(224 * 1.14), int(224 * 1.14))
    assert label.shape == (15,)


def test_dataloader_transform():
    os.environ["DEBUG"] = "True"
    transform = CXRLoader.get_transform([0.2, ] * 5, 0.1)
    # testing outputs
    x = torch.randint(0, 255, (10, 3, 224, 224), dtype=torch.uint8)

    for i in range(5):
        img2 = transform(x)

        assert x.shape == img2.shape


def test_dataloader_advanced_transform():
    # testing outputs
    os.environ["DEBUG"] = "True"
    img = torch.randint(0, 255, (16, 3, 224, 224), dtype=torch.uint8)
    transform = CXRLoader.get_advanced_transform([0.2, ] * 5, 0.1, 2, 9)
    label = torch.randint(0, 2, (16, 14), dtype=torch.float32)
    for i in range(5):
        img2, label2 = transform((img, label))

        assert img2.shape == img.shape, "images are not the same shape!"
        assert label2.shape[1] == 14


def test_dataloader_sampler():
    os.environ["DEBUG"] = "False"
    train = CXRLoader("Train")
    assert len(train.weights) == len(train)


if __name__ == "__main__":
    test_dataloader_transform()
    test_dataloader_advanced_transform()