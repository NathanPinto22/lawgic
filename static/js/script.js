async function sessionValid(caller) {
  console.log(caller);
  return fetch("/session-valid", {
    method: "POST",
    body: "",
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data.valid);
      return data.valid;
    })
    .catch((error) => {
      console.error("Error validating session: ", error);
      return false;
    });
}

function printName(caller) {
  console.log(caller, ": nathan");
}

