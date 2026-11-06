# Origin导入与本轮审计

- 来源：[allen-zhu/kids-video-picks](https://cursor.com/codebase/allen-zhu/kids-video-picks)，`main`。
- 未使用Cursor云端助手；通过只读Origin文件工具取得数据，在本地做资料整理。
- 原库195个文件全部恢复：23个文本文件、172个图片文件。对每个文件按Git blob SHA-1核验，与Origin树一致。大JSON按行续读后也校验成功，未留截断JSON。
- 本地首个提交 `c1960c9` 是完全相同的文件快照；后续提交才增加审核与第28篇。这不是原仓库完整提交历史的镜像。
- 机器可读清单：[origin-import-manifest.json](../data/origin-import-manifest.json)。没有重置、覆盖或修改Origin仓库。
- 旧 `data/catalog.json` 只反映早期161条混合数据，与后来的121条公众号库不同步。本轮以公众号数据为主重建catalog，旧研究保留在 `data/cartoons.json` 和 `docs/web-research/`，不混入本轮推荐计数。
- 重新检查发现旧“51个观看链接”不能等同51部可播正片：多处只返回通用平台页面，部分是片花，部分是官方介绍。已隔离候选地址，所有完整正片播放均未实测。
- 图片全部恢复不等于图片全部准确：原库存在一张文章配图被多部作品重复使用，已标记。新海报源于对应独立评测；没有海报的用明确标记的原创文字封面，不伪装真实海报。

本轮是证据初审，不是438部逐片观影。详见[方法与后续核验清单](wechat/review-method.md)。
