package {
 import flash.display.Sprite;
 import flash.text.TextField;
 import flash.utils.ByteArray;
 import flash.utils.Timer;
 import flash.events.TimerEvent;
 import flash.utils.setTimeout;
 import flash.utils.getDefinitionByName;
 import flash.net.SharedObject;
 import orion.worlds.Item;
 import orion.worlds.Block;
 import orion.worlds.ItemStack;
 import orion.worlds.World;
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
