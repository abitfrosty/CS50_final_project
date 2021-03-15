function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function listener() {
    
}

document.addEventListener('DOMContentLoaded', listener);
