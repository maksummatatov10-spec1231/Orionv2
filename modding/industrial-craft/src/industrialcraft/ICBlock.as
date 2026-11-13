package industrialcraft {
 import flash.geom.Point;
 import orion.worlds.Block;
 import orion.worlds.Material;
 import orion.worlds.Tile;
 public class ICBlock extends Block {
  public function ICBlock(id:int) {
   super(id,Material.IRON);
   setStrength(4); setHard(); setSolid(); setOpaque();
   // Ordinary blocks choose a random one of four atlas variants. This block
   // instead owns three vertical frames, selected per tile by blockData.
   usedSpecialTexture=true; needUpdate=false; needUpdateAnimation=true;
  }
  override public function initBlockData(data:int):int{return 0;}
  override public function setTexturePosition(data:int,pos:Point):void{
   var frame:int=data & 3;pos.x=0;pos.y=frame<=2?frame:0;
  }
  override public function updateAnimation(x:int,y:int,tile:Tile):void{
   var state:MachineState=MachineManager.get(x,y);
   var frame:int=0;
   if(state!=null && state.running && state.canRun())frame=(tile.blockData & 3)==1?2:1;
   tile.blockData=(tile.blockData & ~3)|frame;
  }
 }
}
