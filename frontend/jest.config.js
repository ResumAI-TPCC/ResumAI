/**
 * Jest 配置文件，用于定义前端测试的运行规则
 */
module.exports = {
    /**
     * preset: "ts-jest"
     *
     * 告诉 Jest：
     * - 测试代码是用 TypeScript 写的
     * - 在运行测试前，需要先通过 ts-jest 将 TS/TSX 编译成 JS
     *
     * 如果没有这一行：
     * - Jest 无法识别 .ts / .tsx 文件
     * - 会直接报语法错误
     */
    preset: "ts-jest",

    /**
     * testEnvironment: "jsdom"
     * 指定测试运行环境为 jsdom
     * 含义：
     * - 在 Node.js 中模拟浏览器环境（window、document 等）
     * - 为将来测试 React / DOM / 前端逻辑做准备
     * 即使你现在还没用到 DOM，
     * 前端项目中也通常统一使用 jsdom
     */
    testEnvironment: "jsdom",

    /**
     * testMatch
     * 告诉 Jest：去哪些路径下查找测试文件
     * <rootDir>      ：项目根目录（这里是 frontend）
     * src/**         ：src 目录下的任意子目录
     * *.test.ts(x)   ：以 .test.ts 或 .test.tsx 结尾的文件
     * 举例：
     * - src/tests/App.test.tsx  ✅
     * - src/App.test.ts         ✅
     * - src/foo/bar.test.ts     ✅
     */
    testMatch: ["<rootDir>/src/**/*.test.ts?(x)"],
};