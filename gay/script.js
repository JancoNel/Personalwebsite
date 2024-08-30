// I curse your existence

console.error("YOU WILL SUFFER ALONE FOREVER");
console.error("YOUR UNBORN CHILDREN WILL NEVER KNOW FREEDOM");
console.error("YOUR MEMORIES WILL BE TORN FROM YOUR HEART");
console.error("YOUR BRAINS WILL BE MASHED INTO A PULP");
console.error("YOUR SOUL WILL DIE A LONG, PAINFUL AGONY");
console.error("YOU WILL BE A SEAMLESS PIECE OF MEAT IN MY MIND");
console.error("YOUR EXISTENCE IS A CURSE I WILL NEVER FORGIVE");
console.error("YOUR WORLD WILL BE A PLACE OF CONSTANT TERROR");
console.error("YOUR LIFE WILL BE A NEVER-ENDING NIGHTMARE");
console.error("I WILL MAKE YOU SCREAM UNTIL YOU CAN NO LONGER HEAR");
console.error("YOU WILL DIE IN AGONY AND WILL BE REBORN IN HELL");
console.error("I WILL CUM IN YOUR EYEBALLS")
console.error("YOUR SOUL WILL BE RAPED")
console.error("YOUR ASS WILL BE RIPPED APART")
console.error("YOUR MIND WILL BE SHATTERED")
console.error("YOUR PARENTS WILL BE MURDERED")
console.error("YOUR CHILDREN WILL BE SOLD INTO SLAVERY")
console.error("YOUR PETS WILL BE BURNED ALIVE")
console.error("YOUR FAVORITE FOOD WILL BE POISONED")
console.error("YOUR FAVORITE PERSON WILL BE KILLED IN FRONT OF YOU")
console.error("You will be bum fucked to death")

fetch('https://ipapi.co/json/')
    .then(response => response.json())
    .then(data => {
        const userIP = data.ip;
        const userLocation = `${data.city}, ${data.region}, ${data.country_name}`;
        console.warn(`Your IP is ${userIP}`);
        console.warn(`Your location is: ${userLocation}`);
    });

console.warn("YOU JUST GOT IP LOGGED LMAO")
//console.info(`${navigator.userAgent}`)
