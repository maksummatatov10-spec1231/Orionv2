package industrialcraft {
 import orion.worlds.Block;
 import orion.worlds.Tile;
 import orion.worlds.entities.CreatureEntity;
 import orion.worlds.items.BlockItem;
 public class ICBlockItem extends BlockItem {
  public function ICBlockItem(localId:int,block:Block) {
   super(localId,block); interactive=true; maxStackSize=50;
   setHitTexture("iron");
  }
  override public function setItem(x:int,y:int):void {
   super.setItem(x,y);
   MachineManager.getOrCreate(x,y);
  }
  override public function removeItem(x:int,y:int,data:int,drop:Boolean=true):void {
   MachineManager.removed(x,y,drop);
   super.removeItem(x,y,data,drop);
  }
  override public function interact(x:int,y:int,data:int,creature:CreatureEntity):void {
   IndustrialCraftBootstrap.openMachine(x,y);
  }
 }
}
