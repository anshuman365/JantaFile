// File encryption client-side (WebCrypto API)
async function encryptFile(file, publicKey) {
    const reader = new FileReader();
    
    return new Promise((resolve) => {
        reader.onload = async () => {
            const key = await window.crypto.subtle.importKey(
                'spki',
                parseKey(publicKey),
                { name: 'RSA-OAEP', hash: 'SHA-256' },
                false,
                ['encrypt']
            );
            
            const encrypted = await window.crypto.subtle.encrypt(
                { name: 'RSA-OAEP' },
                key,
                new TextEncoder().encode(reader.result)
            );
            
            resolve(new Blob([encrypted], { type: 'application/octet-stream' }));
        };
        reader.readAsArrayBuffer(file);
    });
}

function parseKey(key) {
    // Convert PEM to ArrayBuffer
    const pemHeader = '-----BEGIN PUBLIC KEY-----';
    const pemFooter = '-----END PUBLIC KEY-----';
    const pemContents = key.replace(pemHeader, '').replace(pemFooter, '').replace(/\s/g, '');
    return Uint8Array.from(atob(pemContents), c => c.charCodeAt(0)).buffer;
}