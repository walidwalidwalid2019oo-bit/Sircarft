const $ = (id) => document.getElementById(id);
const views = ["overview","servers","worlds","billing","settings"];
let servers = [
  {name:"Oakheart SMP",edition:"Java",mode:"Survival"},
  {name:"Moonlit Keep",edition:"Bedrock",mode:"Creative"}
];
function showToast(message){const toast=$("toast");toast.textContent=message;toast.classList.add("show");setTimeout(()=>toast.classList.remove("show"),2600)}
function go(view){views.forEach(v=>{const el=$("view-"+v);if(el)el.classList.toggle("active",v===view)});document.querySelectorAll(".nav-link").forEach(b=>b.classList.toggle("active",b.dataset.view===view));$("breadcrumb-current").textContent=view[0].toUpperCase()+view.slice(1);$("sidebar").classList.remove("open");if(view==="servers")renderServers();window.scrollTo({top:0,behavior:"smooth"})}
document.querySelectorAll(".nav-link").forEach(b=>b.addEventListener("click",()=>go(b.dataset.view)));
document.querySelectorAll("[data-goto]").forEach(b=>b.addEventListener("click",()=>go(b.dataset.goto)));
$("mobile-menu").addEventListener("click",()=>$("sidebar").classList.toggle("open"));
const modal=$("create-modal");
function openModal(mode){modal.classList.add("open");modal.setAttribute("aria-hidden","false");if(mode)$("world-mode").value=mode;setTimeout(()=>$("world-name").focus(),80)}
function closeModal(){modal.classList.remove("open");modal.setAttribute("aria-hidden","true")}
["new-server","realm-create","hero-create"].forEach(id=>$(id).addEventListener("click",()=>openModal()));
$("modal-close").addEventListener("click",closeModal);
modal.addEventListener("click",e=>{if(e.target===modal)closeModal()});
document.querySelectorAll('input[name="edition"]').forEach(input=>input.addEventListener("change",()=>{document.querySelectorAll(".choice").forEach(c=>c.classList.toggle("selected",c.contains(input)&&input.checked))}));
document.querySelectorAll(".library-create").forEach(b=>b.addEventListener("click",()=>openModal(b.dataset.mode)));
function card(server){return `<article class="server-card"><div class="server-cover ${server.edition==="Java"?"cover-forest":"cover-stone"}"><span class="cover-tag">${server.edition.toUpperCase()} EDITION</span><span class="cover-symbol">✧</span><div class="cover-landscape"></div></div><div class="server-card-body"><div class="server-title-row"><div><h3>${escapeHtml(server.name)}</h3><p class="server-address">local-demo.sircarft</p></div><span class="server-state"><i></i> Demo</span></div><div class="server-meta"><span>${server.mode}</span><span>•</span><span>Local preview</span><span class="meta-spacer"></span><span class="server-version">1.21.x</span></div><button class="server-open" data-server="${escapeHtml(server.name)}">Open server details <span>→</span></button></div></article>`}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function renderServers(){const html=servers.map(card).join("");$("all-server-grid").innerHTML=html;$("server-grid").innerHTML=html;$("server-count").textContent=servers.length;document.querySelectorAll("[data-server]").forEach(b=>b.addEventListener("click",()=>showToast(b.dataset.server+" is a visual demo — real hosting is not connected.")))}
$("create-form").addEventListener("submit",e=>{e.preventDefault();const name=$("world-name").value.trim();if(!name)return;const edition=document.querySelector('input[name="edition"]:checked').value;servers.push({name,edition,mode:$("world-mode").value});renderServers();$("create-form").reset();document.querySelectorAll(".choice").forEach((c,i)=>c.classList.toggle("selected",i===0));closeModal();go("servers");showToast("Demo world created in this browser session.")});
renderServers();