function getDecodedCookie(cookieName) {
    const cookies = document.cookie.split(';');
    const replacements = {
        '%22': '"',
        '%3A': ':',
        '%2C': ',',
        '%7B': '{',
        '%7D': '}',
    };

    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');

        if (name === cookieName && value) {
            let decodedValue = value;
            Object.entries(replacements).forEach(([encoded, decoded]) => {
                decodedValue = decodedValue.replaceAll(encoded, decoded);
            });

            return decodedValue;
        }
    }
    return null;
}

if (window.location.hostname === 'boosty.to') {
    const authCookie = getDecodedCookie("auth")
    if (authCookie) {
        const authObj = JSON.parse(authCookie)
        const token = {
            "authorization": authObj.accessToken,
            "expires_in": authObj.expiresAt,
            "full_cookie": `${document.cookie}`
        }
        console.group("You token here")
        console.log(`\nJust copy this text:

        ${btoa(JSON.stringify(token))}
        `)
        console.groupEnd()
        console.log("Do not give this token to anyone")
    } else {
        console.warn("Authorization data could not be found. Are you sure you are logged in?")
    }
} else {
    console.warn("There is", window.location.hostname, ", not boosty.to =)")
}