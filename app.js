const $ = (id) => document.getElementById(id);
const views = ["overview","servers","worlds","billing","settings"];
const STORAGE_KEY = "sircarft.demo.servers.v1";
const DEFAULT_SERVERS = [
  {name:"Oakheart SMP",edition:"Java",mode:"Survival"},
  {name:"Moonlit Keep",edition:"Bedrock",mode:"Creative"}
];
function loadServers(){
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return DEFAULT_SERVERS.map(server=>({...server}));
    const parsed = JSON.parse(saved);
    if (!Array.isArray(parsed)) return DEFAULT_SERVERS.map(server=>({...server}));
    return parsed.filter(server =>
      server && typeof server.name === "string" &&
      ["Java","Bedrock"].includes(server.edition) &&
      ["Survival","Creative","Adventure"].includes(server.mode)
    ).slice(0,50).map(server=>({
      name:server.name.slice(0,24),edition:server.edition,mode:server.mode
    }));
  } catch {
    return DEFAULT_SERVERS.map(server=>({...server}));
  }
}
let servers = loadServers();
function persistServers(){
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(servers));
    return true;
  } catch {
    showToast("Browser storage is unavailable. Demo changes may not survive refresh.");
    return false;
  }
}
function showToast(message){const toast=$("toast");toast.textContent=message;toast.classList.add("show");setTimeout(()=>toast.classList.remove("show"),2600)}
function go(view){views.forEach(v=>{const el=$("view-"+v);if(el)el.classList.toggle("active",v===view)});document.querySelectorAll(".nav-link").forEach(b=>b.classList.toggle("active",b.dataset.view===view));$("breadcrumb-current").textContent=view[0].toUpperCase()+view.slice(1);$("sidebar").classList.remove("open");if(view==="servers")renderServers();window.scrollTo({top:0,behavior:"smooth"})}
document.querySelectorAll(".nav-link").forEach(b=>b.addEventListener("click",()=>go(b.dataset.view)));
document.querySelectorAll("[data-goto]").forEach(b=>b.addEventListener("click",()=>go(b.dataset.goto)));
$("mobile-menu").addEventListener("click",()=>$("sidebar").classList.toggle("open"));
const modal=$("create-modal");
const detailModal=$("server-details-modal");
function openModal(mode){modal.classList.add("open");modal.setAttribute("aria-hidden","false");if(mode)$("world-mode").value=mode;setTimeout(()=>$("world-name").focus(),80)}
function closeModal(){modal.classList.remove("open");modal.setAttribute("aria-hidden","true")}
function closeDetails(){detailModal.classList.remove("open");detailModal.setAttribute("aria-hidden","true")}
function openServerDetails(name){
  const server=servers.find(item=>item.name===name);
  if(!server)return;
  $("detail-name").textContent=server.name;
  $("detail-edition").textContent=server.edition+" Edition";
  $("detail-mode").textContent=server.mode;
  $("detail-status").textContent="Not provisioned";
  $("detail-address").textContent="No IP address assigned";
  detailModal.classList.add("open");
  detailModal.setAttribute("aria-hidden","false");
  $("detail-close").focus();
}
["new-server","realm-create","hero-create"].forEach(id=>$(id).addEventListener("click",()=>openModal()));
$("modal-close").addEventListener("click",closeModal);
modal.addEventListener("click",e=>{if(e.target===modal)closeModal()});
$("detail-close").addEventListener("click",closeDetails);
$("detail-close-action").addEventListener("click",closeDetails);
detailModal.addEventListener("click",e=>{if(e.target===detailModal)closeDetails()});
document.addEventListener("keydown",e=>{if(e.key==="Escape"){if(modal.classList.contains("open"))closeModal();if(detailModal.classList.contains("open"))closeDetails()}});
document.addEventListener("click",e=>{
  const trigger=e.target.closest("[data-server]");
  if(trigger)openServerDetails(trigger.dataset.server);
});
document.querySelectorAll('input[name="edition"]').forEach(input=>input.addEventListener("change",()=>{document.querySelectorAll(".choice").forEach(c=>c.classList.toggle("selected",c.contains(input)&&input.checked))}));
document.querySelectorAll(".library-create").forEach(b=>b.addEventListener("click",()=>openModal(b.dataset.mode)));
function card(server){return `<article class="server-card"><div class="server-cover ${server.edition==="Java"?"cover-forest":"cover-stone"}"><span class="cover-tag">${server.edition.toUpperCase()} EDITION</span><span class="cover-symbol">✧</span><div class="cover-landscape"></div></div><div class="server-card-body"><div class="server-title-row"><div><h3>${escapeHtml(server.name)}</h3><p class="server-address">Local preview · no IP assigned</p></div><span class="server-state"><i></i> Demo</span></div><div class="server-meta"><span>${server.mode}</span><span>•</span><span>Preview only</span><span class="meta-spacer"></span><span class="server-version">1.21.x</span></div><button class="server-open" data-server="${escapeHtml(server.name)}">View world record <span>→</span></button></div></article>`}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function renderServers(){const html=servers.map(card).join("");$("all-server-grid").innerHTML=html;$("server-grid").innerHTML=html;$("server-count").textContent=servers.length;}
$("create-form").addEventListener("submit",e=>{e.preventDefault();const name=$("world-name").value.trim();if(!name)return;if(servers.some(server=>server.name.toLocaleLowerCase()===name.toLocaleLowerCase())){showToast("A world with that name already exists.");return;}const edition=document.querySelector('input[name="edition"]:checked').value;servers.push({name:name.slice(0,24),edition,mode:$("world-mode").value});const persisted=persistServers();renderServers();$("create-form").reset();document.querySelectorAll(".choice").forEach((c,i)=>c.classList.toggle("selected",i===0));closeModal();go("servers");showToast(persisted?"Local preview saved in this browser. No server is running.":"Preview added for this session; browser storage is unavailable.")});
renderServers();
