module.exports = {
    testEnvironment: "jsdom",
    transform: {
        "^.+\\.(t|j)sx?$": "babel-jest",
    },
    moduleFileExtensions: ["ts", "tsx", "js", "jsx"],
};