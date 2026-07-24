v1.4.3主要修复：

1. **收藏夹名称动态等待**

   * 不再固定 3 秒
   * 每 500ms 检测一次
   * 最多等待 10 秒

2. **FID作为唯一数据库索引**

   * 不会因为名称变化产生重复数据

3. **增加“重新识别”按钮**

   * 方便调试 B站动态页面

4. **当前收藏夹独立导出**

   * 不会累计其他收藏夹

5. 保留：

   * TXT
   * CSV
   * JSON
   * 全数据库 JSON

完整代码：

```javascript
// ==UserScript==
// @name         B站收藏夹批量导出工具 v1.4.3
// @namespace    http://tampermonkey.net/
// @version      1.4.3
// @description  B站收藏夹分类导出工具，FID独立存储，修复动态加载识别
// @author       ChatGPT
// @license      MIT
// @match        https://space.bilibili.com/*/favlist*
// @grant        none
// ==/UserScript==


(function(){

'use strict';


// ===============================
// 数据库
// ===============================


let database = JSON.parse(

localStorage.getItem(
"bili_folder_database_v143"
)

|| "{}"

);





// ===============================
// 获取收藏夹信息
// ===============================


function getFolderInfo(){


let fid =
new URLSearchParams(
location.search
)
.get("fid")
||
"";



let name="";



// 当前收藏夹标题

let title =
document.querySelector(
".favlist-info-detail__title-row"
);



if(
title &&
title.innerText.trim()
){

name=
title.innerText.trim();

}





// 左侧激活收藏夹

if(!name){


let active =
document.querySelector(
".vui_sidebar-item--active .vui_sidebar-item-title"
);


if(
active &&
active.innerText.trim()
){

name=
active.innerText.trim();

}

}




// 页面文字备用

if(!name){


let els =
[
...document.querySelectorAll(
".vui_sidebar-item-title"
)

];


for(let e of els){


let t=e.innerText.trim();


if(t){

name=t;

break;

}


}


}





return {

fid:fid,

name:name

};


}









// ===============================
// 等待B站加载
// ===============================


function waitFolder(callback){



let count=0;



let timer=setInterval(()=>{


let info=getFolderInfo();



if(
info.name
&&
info.fid
){


clearInterval(timer);

callback(info);


}



count++;



if(count>20){


clearInterval(timer);


callback({

fid:info.fid,

name:
info.name||
("未知收藏夹_"+info.fid)

});


}



},500);



}









// ===============================
// 初始化
// ===============================


waitFolder(init);






function init(folderInfo){



let fid=
folderInfo.fid;


let folderName=
folderInfo.name;



console.log(
"当前收藏夹:",
folderName,
fid
);





if(!database[fid]){


database[fid]={

name:folderName,

videos:[]

};


}


else{


database[fid].name=
folderName;


}






// ===============================
// 面板
// ===============================


let old=
document.querySelector(
"#biliExportBox"
);


if(old)
old.remove();





let panel=
document.createElement("div");



panel.id=
"biliExportBox";



panel.style.cssText=`

position:fixed;
right:20px;
top:120px;
z-index:999999;

background:white;

padding:15px;

border-radius:10px;

box-shadow:0 0 15px #888;

font-size:14px;

width:300px;

`;





panel.innerHTML=`

<div>

收藏夹:

<br>

<b>
${folderName}
</b>


<br><br>

FID:

${fid}

</div>


<hr>


<button id="refreshFolder">

重新识别

</button>


<button id="scanBili">

扫描当前页面

</button>


<br><br>


<button id="copyDetail">

复制详细

</button>


<button id="copyLink">

复制链接

</button>


<br><br>


<button id="saveTxt">

TXT

</button>


<button id="saveCsv">

CSV

</button>


<button id="saveJson">

JSON

</button>


<br><br>


<button id="clearFolder">

清空当前

</button>


<button id="saveAll">

全部JSON

</button>


<hr>


<div id="countBili">

数量:0

</div>

`;



document.body.appendChild(panel);









function list(){

return database[fid].videos;

}




function saveDB(){

localStorage.setItem(

"bili_folder_database_v143",

JSON.stringify(database)

);

}





function update(){

document.querySelector(
"#countBili"
)
.innerText=
"数量:"+list().length;


saveDB();


}



update();










// ===============================
// 扫描视频
// ===============================


function scan(){


let result=[];



let links=
document.querySelectorAll(
'a[href*="/video/BV"]'
);



let seen=new Set();



links.forEach(a=>{


let m=
a.href.match(
/\/video\/(BV[a-zA-Z0-9]+)/
);



if(!m)
return;



let bvid=m[1];



if(seen.has(bvid))
return;


seen.add(bvid);




let title=

a.querySelector("img")?.alt

||

a.title

||

bvid;





let stats=[

...a.querySelectorAll(
".bili-cover-card__stat span"
)

]
.map(
x=>x.innerText.trim()
);





result.push({

title:title,

bvid:bvid,

views:stats[0]||"",

danmu:stats[1]||"",

duration:stats[2]||"",


url:
"https://www.bilibili.com/video/"+bvid


});


});



return result;


}









// ===============================
// 扫描
// ===============================


document.querySelector(
"#scanBili"
)
.onclick=function(){


let arr=scan();


let add=0;



arr.forEach(v=>{


if(
!list()
.some(
x=>x.bvid===v.bvid
)

){


list().push(v);

add++;

}


});



update();



alert(

"收藏夹:\n"+
folderName+

"\n新增:"
+add+

"\n当前:"
+list().length

);


};









// ===============================
// 重新识别
// ===============================


document.querySelector(
"#refreshFolder"
)
.onclick=function(){


location.reload();


};









function detailText(){


return list().map(v=>{


return `收藏夹：
${folderName}


FID：
${fid}


标题：
${v.title}


BV号：
${v.bvid}


播放量：
${v.views}


弹幕：
${v.danmu}


时长：
${v.duration}


链接：
${v.url}


====================
`;


}).join("\n");


}







function linkText(){

return list()
.map(v=>v.url)
.join("\n");

}









function download(content,name,type){


let blob=
new Blob(
[content],
{
type:type
}
);



let url=
URL.createObjectURL(blob);



let a=document.createElement("a");


a.href=url;


a.download=name;


a.click();



URL.revokeObjectURL(url);


}









document.querySelector(
"#copyDetail"
)
.onclick=function(){


navigator.clipboard.writeText(
detailText()
);


alert(
"复制完成"
);


};






document.querySelector(
"#copyLink"
)
.onclick=function(){


navigator.clipboard.writeText(
linkText()
);


alert(
"复制 "+list().length+" 个链接"
);


};









document.querySelector(
"#saveTxt"
)
.onclick=function(){


download(
detailText(),
folderName+".txt",
"text/plain;charset=utf-8"
);


};









document.querySelector(
"#saveCsv"
)
.onclick=function(){


let csv=
"收藏夹,FID,标题,BV号,播放量,弹幕,时长,链接\n";



list().forEach(v=>{


csv+=

`"${folderName}",`+
`"${fid}",`+
`"${v.title.replace(/"/g,'""')}",`+
`${v.bvid},`+
`${v.views},`+
`${v.danmu},`+
`${v.duration},`+
`${v.url}\n`;



});



download(
csv,
folderName+".csv",
"text/csv;charset=utf-8"
);


};









document.querySelector(
"#saveJson"
)
.onclick=function(){


download(

JSON.stringify(
database[fid],
null,
2
),

folderName+".json",

"application/json"

);


};









document.querySelector(
"#clearFolder"
)
.onclick=function(){


if(confirm(
"清空当前收藏夹缓存?"
)){


database[fid].videos=[];


update();


alert(
"完成"
);


}


};









document.querySelector(
"#saveAll"
)
.onclick=function(){


download(

JSON.stringify(
database,
null,
2
),

"B站全部收藏夹数据库.json",

"application/json"

);


};





}



})();
```

---

测试顺序：

1. 打开：

```
https://space.bilibili.com/你的UID/favlist?fid=3650644310
```

2. 等待面板出现

应该显示：

```
收藏夹:
1、进丨课程

FID:
3650644310
```

3. 点击扫描

显示：

```
新增33
当前33
```

4. 切换：

```
汇丨四足丨
```

刷新后：

应该显示：

```
收藏夹:
汇丨四足丨

FID:
xxxx
```

数量重新为：

```
0
```

而不是33。

如果这个版本稳定，下一步就是 v1.5 自动遍历全部 FID。
