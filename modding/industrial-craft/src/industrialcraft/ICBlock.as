package industrialcraft {
 import orion.worlds.Block;
 import orion.worlds.Material;
 public class ICBlock extends Block {
  public function ICBlock(id:int) {
   super(id,Material.IRON);
   setStrength(4); setHard(); setSolid(); setOpaque();
   needUpdate=false; needUpdateAnimation=false;
  }
 }
}
