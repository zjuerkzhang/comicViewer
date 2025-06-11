const split_count=2;
const magic_number_parser={
    '0':(tmp)=>{
        const type=tmp[1]
        switch(type)
        {
            case 0:
                return {
                    file_type:'jpeg',
                    type:'monga',
                    book_id:tmp[2]*256+tmp[3],
                    page_number:tmp[4]*16777216+tmp[5]*65536+tmp[6]*256+tmp[7],
                }
            case 1:
                return {
                    file_type:'jpeg',
                    type:'other',
                    seed:tmp[2]*16777216+tmp[3]*65536+tmp[4]*256+tmp[5],
                }
            default:
                throw new Error(`unknown type: ${tmp[1]}`)
        }
    },
    '3':(tmp)=>{
        const type=tmp[1]
        switch(type)
        {
            case 0:
                return {
                    file_type:'gif',
                    type:'monga',
                    book_id:tmp[2]*256+tmp[3],
                    page_number:tmp[4]*16777216+tmp[5]*65536+tmp[6]*256+tmp[7],
                }
            case 1:
                return {
                    file_type:'gif',
                    type:'other',
                    seed:tmp[2]*16777216+tmp[3]*65536+tmp[4]*256+tmp[5],
                }
            default:
                throw new Error(`unknown type: ${tmp[1]}`)
        }
    },
}

function get_magic_number_parser(type)
{
    return magic_number_parser[type]
}

const inject_image_magic_number=(tmp)=>{
    switch(tmp[0])
    {
        case 0:
            tmp.set([parseInt("FF",16)],0);
            tmp.set([parseInt("D8",16)],1);
            tmp.set([parseInt("FF",16)],2);
            tmp.set([parseInt("E0",16)],3);
            tmp.set([parseInt("00",16)],4);
            tmp.set([parseInt("10",16)],5);
            tmp.set([parseInt("4A",16)],6);
            tmp.set([parseInt("46",16)],7);
            tmp.set([parseInt("49",16)],8);
            tmp.set([parseInt("46",16)],9);
            tmp.set([parseInt("00",16)],10);
            tmp.set([parseInt("01",16)],11);
            return tmp;
        case 1:
            tmp.set([parseInt("89",16)],0);
            tmp.set([parseInt("50",16)],1);
            tmp.set([parseInt("4E",16)],2);
            tmp.set([parseInt("47",16)],3);
            tmp.set([parseInt("0D",16)],4);
            tmp.set([parseInt("0A",16)],5);
            tmp.set([parseInt("1A",16)],6);
            tmp.set([parseInt("0A",16)],7);
            return tmp;
        case 3:
            tmp.set([parseInt("47",16)],0);
            tmp.set([parseInt("49",16)],1);
            tmp.set([parseInt("46",16)],2);
            tmp.set([parseInt("38",16)],3);
            tmp.set([parseInt("39",16)],4);
            tmp.set([parseInt("61",16)],5);
            return tmp;
    }
}


function convert_jpeg_url_to_binary_url_multiple_hosts(url,hosts)
{
    const split_urls=[];
    const split_origin_url=url.split(".");
    const ext=split_origin_url[split_origin_url.length-1];
    const domain=get_domain_from_url(url)+"/break_2";
    console.log(domain)

    for(let i=0;i<split_count;i++)
    {
        const new_url=url.replace(ext,`b_${i}`).replace(domain,hosts[i]);
        split_urls.push(new_url+"?t=9");
    }
    return split_urls;
}


function get_domain_from_url(url)
{
    var domainRegex=/^(https?:\/\/)?(?:[^@\n]+@)?(?:www\.)?([^:\/\n?]+)/g;
    var matches=domainRegex.exec(url);
    if(matches&&matches.length>0)
    {
        return matches[0];
    }
    return "";
}

function convert_jpeg_url_to_binary_url(url)
{
    const split_urls=[];
    const split_origin_url=url.split(".");
    const ext=split_origin_url[split_origin_url.length-1];
    for(let i=0;i<split_count;i++)
    {
        split_urls.push(url.replace(ext,`b_${i}`));
    }
    return split_urls;
}


async function decrypt(data)
{
    const toUint8Array=dataString=>Uint8Array.from(dataString,c=>c.charCodeAt(0));
    const rawKey=toUint8Array("aaaaaaaaaaaaaaaa");
    const iv=toUint8Array("0123456789aaaaaa");
    const key=await window.crypto.subtle.importKey("raw",rawKey,"AES-CBC",true,["encrypt","decrypt"]);
    const result=await window.crypto.subtle.decrypt({name:"AES-CBC",iv:iv},key,data);
    return result;
}

async function get_url_content(url)
{
    var request=new XMLHttpRequest();
    request.open('GET',`${url}`,true);
    request.responseType="arraybuffer";
    var p2=new Promise((res,rej)=>{
        request.onreadystatechange=async function(){
            if(request.readyState===4&&request.status===200)
            {
                JSON.stringify(request.response);
                res(request.response);
            }
        }
    })
    request.send(null);
    try
    {
        const encryptResponse=await p2;
        const decryptResponse=await decrypt(encryptResponse);
        return decryptResponse;
    }
    catch(e)
    {
        console.error(e.stack);
        console.error(e);
        return ""
    }
}


async function get_urls_content(urls)
{
    const promises=[];
    urls.forEach((e)=>{
        promises.push(get_url_content(e));
    });
    const buffers=await Promise.all(promises);
    return combine_all_bytearray(buffers);
}

async function combine_all_bytearray(buffers)
{
    const total_len=buffers.reduce((acc,cur)=>{
        acc+=cur.byteLength;
        return acc;
    },
    0);

    var tmp=new Uint8Array(total_len);
    const promises=[];
    for(let i=0;i<buffers.length;i++)
    {
        if(i==0)
        {
            promises.push(new Promise((res,_)=>{
                tmp.set(new Uint8Array(buffers[i]),0);
                res(0);
            }));
        }
        else
        {
            promises.push(new Promise((res,_)=>{
                tmp.set(new Uint8Array(buffers[i]),buffers[i-1].byteLength);
                res(0);
            }));
        }
    }
    await Promise.all(promises);
    return tmp;
}


function create_blob(recovered_tmp,magic_number_info)
{
    switch(magic_number_info.file_type)
    {
        case "gif":
            var blob=new Blob([recovered_tmp.buffer],{type:"image/gif"});
            return blob;
        case "jpeg":
        default:
            var blob=new Blob([recovered_tmp.buffer],{type:"image/jpg"});
            return blob;
    }
}


async function recover_img_url_with_multiple_hosts(url,hosts_string)
{
    const b_urls=convert_jpeg_url_to_binary_url_multiple_hosts(url,hosts_string.split(","));
    const urls_contents=await get_urls_content(b_urls);
    const type_number=`${urls_contents[0]}`;
    const magic_number_info=get_magic_number_parser(type_number)(urls_contents);
    const recovered_tmp=inject_image_magic_number(urls_contents);
    var blob=create_blob(recovered_tmp,magic_number_info);
    var url_t=URL.createObjectURL(blob);
    return {
        url_t:url_t,
        blob,
        magic_number_info:magic_number_info
    };
}


async function recover_img_url(url)
{
    const b_urls=convert_jpeg_url_to_binary_url(url);
    const urls_contents=await get_urls_content(b_urls);
    const type_number=`${urls_contents[0]}`;
    const magic_number_info=get_magic_number_parser(type_number)(urls_contents);
    const recovered_tmp=inject_image_magic_number(urls_contents);
    var blob=create_blob(recovered_tmp,magic_number_info);
    var url_t=URL.createObjectURL(blob)
    ;return{url_t:url_t,blob,magic_number_info:magic_number_info};
}



import json
from base64 import b64encode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

data = b"secret"
key = get_random_bytes(16)
cipher = AES.new(key, AES.MODE_CBC)
ct_bytes = cipher.encrypt(pad(data, AES.block_size))
iv = b64encode(cipher.iv).decode('utf-8')
ct = b64encode(ct_bytes).decode('utf-8')
result = json.dumps({'iv':iv, 'ciphertext':ct})
print(result)
'{"iv": "bWRHdzkzVDFJbWNBY0EwSmQ1UXFuQT09", "ciphertext": "VDdxQVo3TFFCbXIzcGpYa1lJbFFZQT09"}'


import json
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# We assume that the key was securely shared beforehand
try:
    b64 = json.loads(json_input)
    iv = b64decode(b64['iv'])
    ct = b64decode(b64['ciphertext'])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    print("The message was: ", pt)
except (ValueError, KeyError):
    print("Incorrect decryption")



ba[0] = 0xff
ba[1] = 0xd8
ba[2] = 0xff
ba[3] = 0xe0
ba[4] = 0x00
ba[5] = 0x10
ba[6] = 0x4a
ba[7] = 0x46
ba[8] = 0x49
ba[9] = 0x46
ba[10] = 0x00
ba[11] = 0x01