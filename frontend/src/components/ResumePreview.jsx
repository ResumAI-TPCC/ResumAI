/**
 * ResumePreview Component - 右侧预览区域
 * 
 * 功能规划:
 * - Resume Preview 标题
 * - Match Score 徽章 (68/100)
 * - 文档预览区域
 * - Generate Polished Resume 开关
 * - Download Polished Resume 按钮
 * 
 * TODO: 后续实现
 */

function ResumePreview() {
  return (
    <aside className="w-80 bg-white border-l border-gray-200 p-6 h-screen">
      <div className="text-gray-400 text-center">
        <p className="font-bold text-lg mb-2">Resume Preview</p>
        <p className="text-sm">TODO: 待实现</p>
        <ul className="text-left text-xs mt-4 space-y-1">
          <li>• Match Score 徽章</li>
          <li>• 文档预览</li>
          <li>• Generate 开关</li>
          <li>• Download 按钮</li>
        </ul>
      </div>
    </aside>
  )
}

export default ResumePreview
