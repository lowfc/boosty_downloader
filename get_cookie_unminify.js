
const full_cookie = `${document.cookie}`

function getCookie(name, cookie) {
  const parts = cookie.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

function parseAuthCookie(e) {
    if (void 0 === e) return;
    let o = e.replaceAll("%7B", "{");
    (o = o.replaceAll("%22", '"')), (o = o.replaceAll("%3A", ":")), (o = o.replaceAll("%2C", ",")), (o = o.replaceAll("%7D", "}"));
    let i = JSON.parse(o).accessToken;
    return void 0 !== i ? "Bearer " + i : void 0;
}

const auth_token = getCookie("auth", full_cookie)
if (auth_token === undefined) {
    console.log("Не получилось найти данные авторизации. Вы точно вошли в аккаунт?")
} else {

console.log(`

Cookie:

${full_cookie}

Authorization:

${parseAuthCookie(auth_token)}

`)

}
