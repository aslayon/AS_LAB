import os
import numpy as np
import torch
import matplotlib.pyplot as plt
import imageio.v2 as imageio

from env.obstacle_env import GridEnvironment
from model.dqn import DQN

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def render_frame(env, path=None, title="Obstacle Agent Evaluation"):
    grid_display = np.zeros(env.grid_size)
    grid_display[env.grid == 1] = 0.7

    x1, y1 = env.small_goal_range[0]
    x2, y2 = env.small_goal_range[1]
    grid_display[x1:x2 + 1, y1:y2 + 1] = 0.3

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.imshow(grid_display, cmap="Greys", alpha=0.8)

    if path is not None and len(path) > 1:
        path_arr = np.array(path)
        ax.plot(path_arr[:, 1], path_arr[:, 0], "b-", alpha=0.7, label="Path")

    ax.plot(env.start_pos[1], env.start_pos[0], "go", markersize=10, label="Start")
    ax.plot(env.agent_pos[1], env.agent_pos[0], "r*", markersize=14, label="Agent")

    heading = int(round(env.heading / 45) * 45) % 360
    dx, dy = env.direction_map.get(heading, (0, 1))
    ax.arrow(
        env.agent_pos[1],
        env.agent_pos[0],
        dy * 0.5,
        dx * 0.5,
        head_width=0.25,
        head_length=0.25,
        fc="red",
        ec="red",
    )

    for i in range(env.grid_size[0]):
        ax.axhline(y=i + 0.5, color="black", linewidth=0.5, alpha=0.2)
    for j in range(env.grid_size[1]):
        ax.axvline(x=j + 0.5, color="black", linewidth=0.5, alpha=0.2)

    ax.set_xticks(range(env.grid_size[1]))
    ax.set_yticks(range(env.grid_size[0]))
    ax.set_title(title)
    ax.legend(loc="upper left")
    ax.grid(False)
    fig.tight_layout()
    return fig


def fig_to_array(fig):
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
    buf = buf.reshape(h, w, 4)
    return buf[:, :, :3]


def run_one_episode(env, model, save_frames=False):
    state = env.reset()
    done = False
    total_reward = 0.0
    path = [env.agent_pos.copy()]
    frames = []

    while not done:
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
        with torch.no_grad():
            q_values = model(state_tensor)
            action = q_values.argmax(dim=1).item()

        next_state, reward, done, _ = env.step(action)
        total_reward += reward
        state = next_state
        path.append(env.agent_pos.copy())

        if save_frames:
            fig = render_frame(
                env,
                path=path,
                title=f"Reward: {total_reward:.2f} | Step: {env.current_steps}"
            )
            frames.append(fig_to_array(fig))
            plt.close(fig)

        if env.current_steps > 120:
            break

    success = env.is_goal(env.agent_pos[0], env.agent_pos[1])

    return {
        "reward": total_reward,
        "steps": env.current_steps,
        "success": success,
        "final_pos": env.agent_pos.copy(),
        "path": path,
        "frames": frames,
        "grid": env.grid.copy(),
        "goal_range": list(env.small_goal_range),
        "heading": env.heading,
        "start_pos": env.start_pos.copy(),
    }


def save_best_episode_artifacts(best_result, gif_path, image_path):
    os.makedirs("results/demos", exist_ok=True)
    os.makedirs("results/plots", exist_ok=True)

    if best_result["frames"]:
        imageio.mimsave(gif_path, best_result["frames"], fps=5)

    # 마지막 장면 다시 그림
    fig, ax = plt.subplots(figsize=(10, 4))
    grid_display = np.zeros(best_result["grid"].shape)
    grid_display[best_result["grid"] == 1] = 0.7

    x1, y1 = best_result["goal_range"][0]
    x2, y2 = best_result["goal_range"][1]
    grid_display[x1:x2 + 1, y1:y2 + 1] = 0.3
    ax.imshow(grid_display, cmap="Greys", alpha=0.8)

    path_arr = np.array(best_result["path"])
    if len(path_arr) > 1:
        ax.plot(path_arr[:, 1], path_arr[:, 0], "b-", alpha=0.7, label="Path")

    ax.plot(best_result["start_pos"][1], best_result["start_pos"][0], "go", markersize=10, label="Start")
    ax.plot(best_result["final_pos"][1], best_result["final_pos"][0], "r*", markersize=14, label="Agent")

    for i in range(grid_display.shape[0]):
        ax.axhline(y=i + 0.5, color="black", linewidth=0.5, alpha=0.2)
    for j in range(grid_display.shape[1]):
        ax.axvline(x=j + 0.5, color="black", linewidth=0.5, alpha=0.2)

    ax.set_xticks(range(grid_display.shape[1]))
    ax.set_yticks(range(grid_display.shape[0]))
    ax.set_title(
        f"Best Episode | Reward: {best_result['reward']:.2f} | "
        f"Steps: {best_result['steps']} | Success: {best_result['success']}"
    )
    ax.legend(loc="upper left")
    ax.grid(False)
    fig.tight_layout()
    fig.savefig(image_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def evaluate_agent(
    model_path="results/models/best_obstacle_model.pth",
    num_eval_episodes=30,
    gif_path="results/demos/obstacle_best_demo.gif",
    image_path="results/plots/obstacle_best_path.png",
):
    env = GridEnvironment()
    state_dim = len(env.reset())
    action_dim = 3

    model = DQN(state_dim, action_dim).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    results = []
    best_result = None

    for episode_idx in range(num_eval_episodes):
        result = run_one_episode(
            env,
            model,
            save_frames=True,
        )
        results.append(result)

        if best_result is None:
            best_result = result
        else:
            # 성공 우선, 성공이면 reward 높은 것 선택
            if result["success"] and not best_result["success"]:
                best_result = result
            elif result["success"] == best_result["success"] and result["reward"] > best_result["reward"]:
                best_result = result

        print(
            f"[Eval {episode_idx + 1:02d}/{num_eval_episodes}] "
            f"Reward: {result['reward']:.2f} | "
            f"Steps: {result['steps']} | "
            f"Success: {result['success']} | "
            f"Final pos: {result['final_pos']}"
        )

    rewards = [r["reward"] for r in results]
    steps = [r["steps"] for r in results]
    success_rate = sum(r["success"] for r in results) / len(results)

    save_best_episode_artifacts(best_result, gif_path, image_path)

    print("\n=== Evaluation Summary ===")
    print(f"Episodes       : {num_eval_episodes}")
    print(f"Success rate   : {success_rate * 100:.1f}%")
    print(f"Average reward : {np.mean(rewards):.2f}")
    print(f"Average steps  : {np.mean(steps):.2f}")
    print(f"Best reward    : {best_result['reward']:.2f}")
    print(f"Best success   : {best_result['success']}")
    print(f"Saved image    : {image_path}")
    print(f"Saved gif      : {gif_path}")


if __name__ == "__main__":
    evaluate_agent()