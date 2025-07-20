#该文件是为了获取OpenNewsArchive的新闻数据 文件为wrac格式，下载至指定文件夹
#注意根据实际情况 输入对应的AK/SK，并修改响应的保存地址
pip install openxlab #安装

pip install -U openxlab #版本升级

import openxlab
openxlab.login(ak=<Access Key>, sk=<Secret Key>) #进行登录，输入对应的AK/SK

from openxlab.dataset import info
info(dataset_repo='OpenDataLab/OpenNewsArchive') #数据集信息及文件列表查看

from openxlab.dataset import get
get(dataset_repo='OpenDataLab/OpenNewsArchive', target_path='/path/to/local/folder/')  # 数据集下载

from openxlab.dataset import download
download(dataset_repo='OpenDataLab/OpenNewsArchive',source_path='/README.md', target_path='/path/to/local/folder') #数据集文件下载