<?php
// Function to get the visitor's IP address
function getUserIP() {
    if (!empty($_SERVER['HTTP_CLIENT_IP'])) {
        // Check if the IP is passed from a shared internet
        $ip = $_SERVER['HTTP_CLIENT_IP'];
    } elseif (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        // Check if the IP is passed from a proxy
        $ip = $_SERVER['HTTP_X_FORWARDED_FOR'];
    } else {
        // Get the IP address from remote address
        $ip = $_SERVER['REMOTE_ADDR'];
    }
    return $ip;
}

// Function to send log data to the Discord webhook
function sendToWebhook($data) {
    $webhookURL = 'https://discord.com/api/webhooks/1264556800816975994/HUNGVeu8vKM1hgVGvDm1ATKw-jNk-AsYl6_WgjI3fMXVCYGpG7kF1ed2lN7IR2Ntvpvh';
    
    $payload = json_encode([
        'content' => "Visitor Log\n" .
                     "IP Address: " . $data['IP Address'] . "\n" .
                     "User Agent: " . $data['User Agent'] . "\n" .
                     "Date and Time: " . $data['Date and Time']
    ]);

    $ch = curl_init($webhookURL);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Content-Length: ' . strlen($payload)
    ]);

    $response = curl_exec($ch);
    curl_close($ch);

    if ($response === false) {
        error_log('Failed to send log to Discord webhook.');
    }
}

// Collect log data
$logData = [
    'IP Address' => getUserIP(),
    'User Agent' => $_SERVER['HTTP_USER_AGENT'],
    'Date and Time' => date('Y-m-d H:i:s')
];

// Send log data to the Discord webhook
sendToWebhook($logData);
?>
