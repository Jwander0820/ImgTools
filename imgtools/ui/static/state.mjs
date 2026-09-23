export const CATEGORY_LABELS = {
  all: '全部', metadata: '資訊', rename: '重新命名', pdf: 'PDF',
  merge: '合併', tif: 'TIF', gif: 'GIF', video: '影片', crop: '裁切', watermark: '浮水印',
};

export const CATEGORY_ICONS = {
  metadata: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 10v6m0-9h.01"/></svg>',
  rename: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h10m-3-3 3 3-3 3M20 17H10m3-3-3 3 3 3"/></svg>',
  pdf: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h8l4 4v14H6zM14 3v5h4M9 13h6M9 17h6"/></svg>',
  merge: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="11" height="11" rx="2"/><path d="M8 19h11a2 2 0 0 0 2-2V8M6 13l3-3 3 3"/></svg>',
  tif: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h14v16H5zM8 8h8M8 12h8M8 16h5"/></svg>',
  gif: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 15 3-3 2 2 2-2 3 3M8 8h.01M16 8h.01"/></svg>',
  video: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m10 9 5 3-5 3z"/></svg>',
  crop: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3v14a2 2 0 0 0 2 2h12M3 7h14a2 2 0 0 1 2 2v12"/></svg>',
  watermark: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 18 12 4l8 14M7 13h10M6 21h12"/></svg>',
};

const ACTION_ICON_FILES = Object.freeze({
  'merge.dialogue_stack': 'dialogue-stack.svg',
  'merge.stack_vertical': 'vertical-stack.svg',
  'watermark.text': 'watermark.svg',
  'watermark.batch_text': 'watermark.svg',
  'pdf.render_page': 'pdf-to-png.svg',
  'pdf.render_all_pages': 'pdf-to-png.svg',
});

export function iconForTool(tool) {
  const file = ACTION_ICON_FILES[tool.action];
  return file
    ? `<img src="${new URL(`./shared/icons/${file}`, import.meta.url).href}" width="24" height="24" alt="">`
    : CATEGORY_ICONS[tool.category] || CATEGORY_ICONS.merge;
}

export let tools = [];
export let selected = null;
export let activeCategory = 'all';
export let searchTerm = '';
export let outputNaming = 'fixed';
export let preferences = {
  pinned_actions: [], usage: {}, quick_actions: [], max_pinned: 8,
  pdf_default_dpi: 192, output_naming: 'fixed',
};
export const formState = {};
export const previewImages = new Map();
export const previewErrors = new Map();
export const previewPendingPaths = new Set();
export const previewRequestTimers = new Map();

export const $ = (id) => document.getElementById(id);


export function setTools(value) { tools = value; }

export function setSelected(value) { selected = value; }

export function setActiveCategory(value) { activeCategory = value; }

export function setSearchTerm(value) { searchTerm = value; }

export function setOutputNamingValue(value) { outputNaming = value; }

export function setPreferences(value) { preferences = value; }
