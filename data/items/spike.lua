-- 尖刺陷阱功能脚本
-- 当玩家触碰尖刺时触发死亡

function on_touch(player, item, map_data)
    -- 杀死玩家
    player.alive = false
    return true
end

function on_update(item, dt)
    -- 尖刺不需要每帧更新
end

function on_draw(item, screen, x, y, tile_size)
    -- 使用纹理绘制，返回false让系统默认绘制
    return false
end
