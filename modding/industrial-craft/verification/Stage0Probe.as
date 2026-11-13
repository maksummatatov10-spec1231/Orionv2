package {
 import flash.display.Sprite;
 import flash.text.TextField;
 import flash.utils.ByteArray;
 import flash.utils.Timer;
 import flash.events.TimerEvent;
 import flash.utils.setTimeout;
 import flash.utils.getTimer;
 import flash.utils.getDefinitionByName;
 import flash.net.SharedObject;
 import orion.worlds.Item;
 import orion.worlds.Block;
 import orion.worlds.ItemStack;
 import orion.worlds.World;
 import orion.worlds.items.blocks.TreeItem;
 public class Stage0Probe extends Sprite {
  public static var _started:Boolean=start();
  private static const MODE:String="__MODE__";
  private static var tries:int=0;
  private static var mx:int; private static var my:int; private static var bx:int; private static var by:int;
  private static var debug:TextField;
  public static function start():Boolean{
   // Test-only: request enough local storage for Orion's world save before the menu.
   try{var so:SharedObject=SharedObject.getLocal("world");trace("IC_TEST_STORAGE "+so.flush(2*1024*1024));}catch(e:Error){trace("IC_TEST_STORAGE_ERROR "+e.message);}
   setTimeout(check,2000);return true;
  }
  private static function check():void {
   tries++;
   try {
    var C:* =getDefinitionByName("Context");
    if(C.game==null || C.world==null || C.world.tilesX<=0 || C.game.player==null || C.game.player.center.x<=0){if(tries<1200)setTimeout(check,500);return;}
    installDebug(C);
    auditIds();
    var B:* =getDefinitionByName("industrialcraft.ContentRegistry");
    var M:* =getDefinitionByName("industrialcraft.MachineManager");
    var w:World=C.world;var px:int=int(C.game.player.center.x/32);var py:int=int(C.game.player.center.y/32);
    if(MODE=="reload"){setTimeout(verifyReload,1200);return;}
    if(MODE=="resin"){setTimeout(verifyResin,1200);return;}
    if(MODE=="timing"){setTimeout(verifyTiming,1200);return;}
    // Test-only grant and site preparation. Not present in dev/release content.
    var gy:int=py;for(var yy:int=py;yy<py+12;yy++){var t:* =w.tiles[px+yy*w.tilesX];if(t.blockId!=0 && Block.BLOCKS[t.blockId].hard){gy=yy;break;}}
    mx=px+2;my=gy-1;bx=mx+3;by=my;
    C.game.player.inventory.add(new ItemStack(Item.RESIN,0,3));
    C.game.player.inventory.add(new ItemStack(Item.COBBLESTONE,0,8));
    C.game.player.inventory.add(new ItemStack(Item.WORKBENCH,0,1));
    w.setBlock(mx,my,B.PROBE_BLOCK);M.getOrCreate(mx,my);
    var s:* =M.get(mx,my);s.items[0]=new ItemStack(Item.RESIN,0,2);s.running=true;
    w.setBlock(bx,by,B.PROBE_BLOCK);M.getOrCreate(bx,by);
    var s2:* =M.get(bx,by);s2.items[0]=new ItemStack(Item.RESIN,0,1);s2.items[1]=new ItemStack(B.PROBE,0,1);
    trace("IC_TEST_SETUP panel="+mx+","+my+" break="+bx+","+by);
    var ba:ByteArray=new ByteArray();var bootstrap:* =getDefinitionByName("industrialcraft.IndustrialCraftBootstrap");
    bootstrap.saveWorld(w,ba);ba.position=0;bootstrap.loadWorld(w,ba);
    trace("IC_TEST_SAVE_ROUNDTRIP machines="+M.count());
    setTimeout(inspect,6500);
   } catch(e:Error){trace("IC_TEST_ERROR "+e.name+" "+e.message+"\n"+e.getStackTrace());}
  }
  private static function inspect():void {
   try {
    var C:* =getDefinitionByName("Context");var B:* =getDefinitionByName("industrialcraft.ContentRegistry");var M:* =getDefinitionByName("industrialcraft.MachineManager");var w:World=C.world;
    var s:* =M.get(mx,my);trace("IC_TEST_TICK completed="+s.completed+" running="+s.running+" output="+(s.items[1]==null?0:s.items[1].count));
    var before:int=w.entitiesOnGround.length;B.PROBE_BLOCK_ITEM.removeItem(bx,by,0,true);var after:int=w.entitiesOnGround.length;
    trace("IC_TEST_BREAK tile="+w.tiles[bx+by*w.tilesX].blockId+" machines="+M.count()+" dropsBefore="+before+" dropsAfter="+after);
    s.running=false;storeExpected(s);
    C.game.showInventory_Crafting(1);trace("IC_TEST_OPEN_WORKBENCH");
   } catch(e:Error){trace("IC_TEST_INSPECT_ERROR "+e.name+" "+e.message+"\n"+e.getStackTrace());}
  }
  private static function verifyTiming():void {
   try {
    var C:* =getDefinitionByName("Context");var B:* =getDefinitionByName("industrialcraft.ContentRegistry");var M:* =getDefinitionByName("industrialcraft.MachineManager");
    var w:World=C.world;var px:int=int(C.game.player.center.x/32);var py:int=int(C.game.player.center.y/32);
    var x:int=px+3;var y:int=py-2;
    w.setBlock(x,y,B.PROBE_BLOCK);var s:* =M.getOrCreate(x,y);
    s.items[0]=new ItemStack(Item.RESIN,0,1);s.running=true;
    var start:int=getTimer();
    trace("IC_TIMING_START x="+x+" y="+y+" blockData="+w.tiles[x+y*w.tilesX].blockData);
    setTimeout(function():void {trace("IC_TIMING_3S completed="+s.completed+" progress="+s.progress+" frame="+(w.tiles[x+y*w.tilesX].blockData & 3)+" elapsed="+(getTimer()-start));},3000);
    setTimeout(function():void {var ms:int=getTimer()-start;trace("IC_TIMING_"+(s.completed==1?"PASS":"FAIL")+" completed="+s.completed+" progress="+s.progress+" elapsed="+ms);},5600);
   } catch(e:Error){trace("IC_TIMING_ERROR "+e.name+" "+e.message+"\n"+e.getStackTrace());}
  }
  private static function countNewResin(w:World,start:int):int {
   var n:int=0;for(var i:int=start;i<w.entitiesOnGround.length;i++){var e:* = w.entitiesOnGround[i];if(e.itemStack!=null && e.itemStack.item==Item.RESIN)n+=e.itemStack.count;}return n;
  }
  private static function verifyResin():void {
   try {
    var C:* =getDefinitionByName("Context");var w:World=C.world;var bootstrap:* =getDefinitionByName("industrialcraft.IndustrialCraftBootstrap");
    var px:int=int(C.game.player.center.x/32);var py:int=int(C.game.player.center.y/32);
    trace("IC_TEST_RESIN_NAME_"+(Item.RESIN.name=="Резина"?"FAIL":"PASS")+" id="+Item.RESIN.id+" name="+Item.RESIN.name+" inventory="+C.game.player.inventory.count(Item.RESIN));
    var tx:int=-1;var ty:int=-1;var data:int=0;
    for(var dy:int=-18;dy<=4 && tx<0;dy++){for(var dx:int=-18;dx<=18;dx++){var x:int=px+dx;var y:int=py+dy;if(x<1||y<2||x>=w.tilesX-1||y>=w.tilesY-1)continue;var t:* = w.tiles[x+y*w.tilesX];if(t.blockId!=Block.TREE.id||!TreeItem.isTrunk(t.blockData))continue;var above:* = w.tiles[x+(y-1)*w.tilesX];if(above.blockId==Block.TREE.id&&TreeItem.isTrunk(above.blockData))continue;tx=x;ty=y;data=t.blockData;break;}}
    if(tx<0){trace("IC_TEST_RESIN_FAIL no natural trunk near player");return;}
    var before:int=w.entitiesOnGround.length;var first:int=0;var finalData:int=data;
    if(data<=11){Item.TREE.removeItem(tx,ty,data,true);first=countNewResin(w,before);finalData=w.tiles[tx+ty*w.tilesX].blockData;before=w.entitiesOnGround.length;}
    Item.TREE.removeItem(tx,ty,finalData,true);var resin:int=countNewResin(w,before);
    // Felling a base trunk can cascade through the whole trunk; every destroyed
    // trunk segment legitimately drops one resin. Require at least one, no first-hit drop.
    var ok:Boolean=resin>=1&&first==0&&w.tiles[tx+ty*w.tilesX].blockId==0;
    trace("IC_TEST_TRUNK_"+(ok?"PASS":"FAIL")+" x="+tx+" y="+ty+" data="+data+" finalData="+finalData+" firstHitResin="+first+" resin="+resin+" tileAfter="+w.tiles[tx+ty*w.tilesX].blockId);
    var bx:int=-1;var by:int=-1;var bd:int=0;
    for(var yy:int=py-18;yy<=py+4 && bx<0;yy++){for(var xx:int=px-18;xx<=px+18;xx++){if(xx<1||yy<1||xx>=w.tilesX-1||yy>=w.tilesY-1)continue;var bt:* = w.tiles[xx+yy*w.tilesX];if(bt.blockId==Block.TREE.id&&bt.blockData>=4&&bt.blockData<=11&&!TreeItem.isTrunk(bt.blockData)){bx=xx;by=yy;bd=bt.blockData;break;}}}
    if(bx>=0){before=w.entitiesOnGround.length;Item.TREE.removeItem(bx,by,bd,true);resin=countNewResin(w,before);trace("IC_TEST_BRANCH_"+(resin==0?"PASS":"FAIL")+" x="+bx+" y="+by+" data="+bd+" resin="+resin);}else trace("IC_TEST_BRANCH_SKIP no branch");
    before=w.entitiesOnGround.length;bootstrap.dropTreeResin(tx,ty,data,false);bootstrap.dropTreeResin(tx,ty,4,true);bootstrap.dropTreeResin(tx,ty,11,true);resin=countNewResin(w,before);
    trace("IC_TEST_RESIN_GUARDS_"+(resin==0?"PASS":"FAIL")+" dropFalseBranchFirstHit="+resin);
    trace("IC_TEST_RESIN_SCREEN x="+int(tx*32-C.game.screen.x+16)+" y="+int(ty*32-C.game.screen.y+16));
   } catch(e:Error){trace("IC_TEST_RESIN_ERROR "+e.name+" "+e.message+"\n"+e.getStackTrace());}
  }
  private static function storeExpected(s:*):void {
   var so:SharedObject=SharedObject.getLocal("ic_stage0_expected");
   so.data.x=mx;so.data.y=my;so.data.progress=s.progress;so.data.completed=s.completed;so.data.running=s.running;
   so.data.input=s.items[0]==null?0:s.items[0].count;so.data.output=s.items[1]==null?0:s.items[1].count;so.flush();
   trace("IC_TEST_EXPECTED x="+mx+" y="+my+" progress="+s.progress+" completed="+s.completed+" input="+so.data.input+" output="+so.data.output);
  }
  private static function verifyReload():void {
   try {
    var C:* =getDefinitionByName("Context");var M:* =getDefinitionByName("industrialcraft.MachineManager");var bootstrap:* =getDefinitionByName("industrialcraft.IndustrialCraftBootstrap");var w:World=C.world;
    var so:SharedObject=SharedObject.getLocal("ic_stage0_expected");mx=int(so.data.x);my=int(so.data.y);
    var s:* =M.get(mx,my);
    if(s==null){trace("IC_TEST_RELOAD_FAIL missing machine");return;}
    var ok:Boolean=s.progress==int(so.data.progress) && s.completed==int(so.data.completed) && s.running==Boolean(so.data.running) && (s.items[0]==null?0:s.items[0].count)==int(so.data.input) && (s.items[1]==null?0:s.items[1].count)==int(so.data.output);
    trace("IC_TEST_RELOAD_"+(ok?"PASS":"FAIL")+" x="+mx+" y="+my+" progress="+s.progress+" completed="+s.completed+" running="+s.running+" input="+(s.items[0]==null?0:s.items[0].count)+" output="+(s.items[1]==null?0:s.items[1].count));
    // Exercise the real full and partial World serializers, then restore the live manager from each IC section.
    var full:ByteArray=new ByteArray();w.save(full);var fp:int=findMagic(full);
    if(fp<0)trace("IC_TEST_FULL_SAVE_FAIL magic missing");else{full.position=fp;bootstrap.loadWorld(w,full);trace("IC_TEST_FULL_SAVE count="+M.count());}
    var first:ByteArray=new ByteArray();var second:ByteArray=new ByteArray();w.savePartial(first,second);
    var combined:ByteArray=new ByteArray();first.position=0;combined.writeBytes(first);for(var i:int=0;i<w.tilesDataPartial.length;i++)combined.writeInt(w.tilesDataPartial[i]);second.position=0;combined.writeBytes(second);
    var pp:int=findMagic(combined);if(pp<0)trace("IC_TEST_PARTIAL_SAVE_FAIL magic missing");else{combined.position=pp;bootstrap.loadWorld(w,combined);trace("IC_TEST_PARTIAL_SAVE count="+M.count());}
    setTimeout(function():void{bootstrap.openMachine(mx,my);},800);
   } catch(e:Error){trace("IC_TEST_RELOAD_ERROR "+e.name+" "+e.message+"\n"+e.getStackTrace());}
  }
  private static function findMagic(b:ByteArray):int {for(var i:int=0;i<=b.length-4;i++){b.position=i;if(b.readUnsignedInt()==0x49435731)return i;}return -1;}
  private static function auditIds():void {
   var freeItems:int=0;var freeBlocks:int=0;var ranges:Array=[];var start:int=-1;
   for(var i:int=1;i<Block.BLOCKS.length;i++){if(Block.BLOCKS[i]==null){freeBlocks++;if(i!=239){if(start<0)start=i;}else{if(start>=0){ranges.push(start+"-"+(i-1));start=-1;}} }else{if(start>=0){ranges.push(start+"-"+(i-1));start=-1;}}}
   if(start>=0)ranges.push(start+"-"+(Block.BLOCKS.length-1));
   for(var j:int=0;j<Item.ITEMS.length;j++)if(Item.ITEMS[j]==null && j!=1242 && j!=495)freeItems++;
   trace("IC_TEST_ID_AUDIT freeItemsBefore="+freeItems+" freeBlocksBefore="+freeBlocks+" blockRanges="+ranges.join(","));
  }
  private static function installDebug(C:*):void {
   debug=new TextField();debug.x=8;debug.y=70;debug.width=1260;debug.height=34;debug.multiline=false;debug.background=true;debug.backgroundColor=0x102020;debug.textColor=0xffffff;debug.text="IC test "+MODE;C.app.addChild(debug);
   var timer:Timer=new Timer(400);timer.addEventListener(TimerEvent.TIMER,function(e:TimerEvent):void{updateDebug(C);});timer.start();updateDebug(C);
  }
  private static function updateDebug(C:*):void {
   try{
    if(C.game==null || C.game.player==null)return;
    var M:* =getDefinitionByName("industrialcraft.MachineManager");
    var px:int=int(C.game.player.center.x/32);var py:int=int(C.game.player.center.y/32);
    var tx:int=int((C.input.mouseX+C.game.screen.x)/32);var ty:int=int((C.input.mouseY+C.game.screen.y)/32);
    var idx:int=C.game.controller.selectedItemIndex;var st:* =C.game.player.inventory.items[idx];
    var blockId:int=(tx>=0&&ty>=0&&tx<C.world.tilesX&&ty<C.world.tilesY)?C.world.tiles[tx+ty*C.world.tilesX].blockId:-1;
    debug.text="IC test "+MODE+" | player="+px+","+py+" | mouseTile="+tx+","+ty+" block="+blockId+" | slot="+idx+" item="+(st==null?0:st.item.id)+" | machines="+M.count()+" | pause="+C.game.gameLoopPause+" | panel="+mx+","+my;
   }catch(e:Error){debug.text="IC debug error "+e.message;}
  }
 }
}
