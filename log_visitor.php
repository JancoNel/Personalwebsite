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

// Function to create a unique file name
function createUniqueFileName($ip) {
    $directory = 'info/';
    $baseName = $directory . $ip;
    $fileName = $baseName . '.txt';
    $counter = 1;
    
    while (file_exists($fileName)) {
        $fileName = $baseName . '_' . $counter . '.txt';
        $counter++;
    }
    
    return $fileName;
}

// Create the directory if it doesn't exist
if (!file_exists('info')) {
    mkdir('info', 0777, true);
}

$ip = getUserIP();
$fileName = createUniqueFileName($ip);
$file = fopen($fileName, 'w');

// Log visitor information
$logData = [
    'IP Address' => $ip,
    'User Agent' => $_SERVER['HTTP_USER_AGENT'],
    'Date and Time' => date('Y-m-d H:i:s')
];

foreach ($logData as $key => $value) {
    fwrite($file, $key . ': ' . $value . "\n");
}

fclose($file);
?>
