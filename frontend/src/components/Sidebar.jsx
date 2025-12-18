/**
 * Sidebar Component - 左侧边栏
 * 
 * 功能规划:
 * - ResumAI Logo
 * - Company Name 输入框
 * - Job Title 输入框
 * - Job Description (JD) 文本区域
 * - Clear JD 按钮
 * - Resume Upload 上传区域
 * - Clear Session 链接
 * 
 * TODO: 后续实现
 */

function Sidebar() {
  return (
    <aside className="w-72 bg-white border-r border-gray-200 p-6 h-screen">
      <div className="text-gray-400 text-center">
        <p className="font-bold text-lg mb-2">Sidebar</p>
        <p className="text-sm">TODO: 待实现</p>
        <ul className="text-left text-xs mt-4 space-y-1">
          <li>• Logo</li>
          <li>• Company Name</li>
          <li>• Job Title</li>
          <li>• Job Description</li>
          <li>• Resume Upload</li>
          <li>• Clear Session</li>
        </ul>
      </div>
    </aside>
  )
}

export default Sidebar
