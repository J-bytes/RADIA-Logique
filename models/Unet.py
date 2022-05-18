"""
Inspired, with part simply taken directly from
https://github.com/mkisantal/backboned-unet/blob/master/backboned_unet/unet.py
"""


import torch
from custom_utils import set_parameter_requires_grad


class UpsampleBlock(torch.torch.nn.Module):

    # TODO: separate parametric and non-parametric classes?
    # TODO: skip connection concatenated OR added

    def __init__(self, ch_in, ch_out=None, skip_in=0, use_bn=True, parametric=False):
        super(UpsampleBlock, self).__init__()

        self.parametric = parametric
        ch_out = int(ch_in / 2) if ch_out is None else ch_out

        # first convolution: either transposed conv, or conv following the skip connection
        if parametric:
            # versions: kernel=4 padding=1, kernel=2 padding=0
            self.up = torch.nn.ConvTranspose2d(
                in_channels=ch_in,
                out_channels=ch_out,
                kernel_size=(4, 4),
                stride=2,
                padding=1,
                output_padding=0,
                bias=(not use_bn),
            )
            self.bn1 = torch.nn.BatchNorm2d(ch_out) if use_bn else None
        else:
            self.up = None
            ch_in = ch_in + skip_in
            self.conv1 = torch.nn.Conv2d(
                in_channels=ch_in,
                out_channels=ch_out,
                kernel_size=(3, 3),
                stride=1,
                padding=1,
                bias=(not use_bn),
            )
            self.bn1 = torch.nn.BatchNorm2d(ch_out) if use_bn else None

        self.relu = torch.nn.ReLU(inplace=True)

        # second convolution
        conv2_in = ch_out if not parametric else ch_out + skip_in
        self.conv2 = torch.nn.Conv2d(
            in_channels=conv2_in,
            out_channels=ch_out,
            kernel_size=(3, 3),
            stride=1,
            padding=1,
            bias=(not use_bn),
        )
        self.bn2 = torch.nn.BatchNorm2d(ch_out) if use_bn else None

    def forward(self, x, skip_connection=None):

        x = (
            self.up(x)
            if self.parametric
            else torch.nn.functional.interpolate(
                x, size=None, scale_factor=2, mode="bilinear", align_corners=None
            )
        )
        if self.parametric:
            x = self.bn1(x) if self.bn1 is not None else x
            x = self.relu(x)

        if skip_connection is not None:
            x = torch.cat([x, skip_connection], dim=1)

        if not self.parametric:
            x = self.conv1(x)
            x = self.bn1(x) if self.bn1 is not None else x
            x = self.relu(x)
        x = self.conv2(x)
        x = self.bn2(x) if self.bn2 is not None else x
        x = self.relu(x)

        return x


class Unet(torch.torch.nn.Module):
    def __init__(
        self,
        backbone_name="densenet101",
        encoder_freeze=False,
        pretrained=True,
        decoder_filters=[4, 8, 16, 32, 64, 128, 256, 512],
        classes=14,
    ):
        super(Unet, self).__init__()

        self.classes = classes

        # lets define the decoder

        self.backbone, self.features_name = self.get_backbone(backbone_name, pretrained)
        _, features = self.forward_encoder(
            torch.randint(0, 255, (1, 3, 320, 320)).float()
        )  # dynamically look at the channels of the model
        self.features = features
        previous_size = 0
        temp = []
        for feature_name, feature in zip(self.features_name, features.values()):
            if feature.shape[2] != previous_size:
                temp.append(
                    feature_name
                )  # only keep feature that change the size of the input
                previous_size = feature.shape[2]
        self.features_name = temp
        self.skips_in = [features[feature].shape[1] for feature in self.features_name]

        self.decoder_filters = decoder_filters[: len(self.features_name)][::-1]
        self.upsample_blocks = self.get_decoder(decoder_filters)

        if encoder_freeze:
            set_parameter_requires_grad(self.backbone, -1)

    def forward_encoder(self, x):
        features = {}
        for name, child in self.backbone.named_children():
            x = child(x)
            if name in self.features_name:
                features[name] = x
        return x, features

    def get_backbone(self, backbone_name, pretrained):
        features_name = []
        backbone = torch.hub.load(
            "pytorch/vision:v0.10.0", backbone_name, pretrained=pretrained
        )
        for item_name, item in backbone.features._modules.items():

            if len(item._modules) > 0:  # if its a block the author implemented
                features_name.append(item_name)

        return backbone.features, features_name

    def get_decoder(self, decoder_filters):
        # self.backbone=backbone.features
        upsample_blocks = torch.nn.ModuleList()

        in_channels = list(self.features.values())[::-1][0].shape[1]
        for ex, skip_in in enumerate(self.skips_in[::-1][1::]):
            print(ex, in_channels, skip_in)
            upsample_blocks.append(UpsampleBlock(in_channels, skip_in=skip_in))
            in_channels = int((in_channels / 2))

        # final_layer = UpsampleBlock(in_channels,ch_out=3,skip_in=0)
        return upsample_blocks

    def forward_decoder(self, x, features):

        for block, feature_name in zip(
            self.upsample_blocks, self.features_name[::-1][1::]
        ):
            skip_connection = features[feature_name]
            x = block(x, skip_connection)

        return x

    def forward(self, x):
        x, self.features = self.forward_encoder(x)
        x = self.forward_decoder(x, self.features)
        return x
