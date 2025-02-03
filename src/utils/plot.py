import os
import wandb
import numpy as np
from matplotlib import pyplot as plt

colors = ["blue", "orange", "green", "purple", "olive", "red", "magenta", "black"]


def plot_ax(ax, array, title=None, fontsize=15, cmap="bwr",vmin = None, vmax=None):
    if vmax is None:
        vmax = np.max(np.abs(array))
    if vmin is None:
        vmin = min(-vmax, 2*vmax)
    im = ax.imshow(array, cmap=cmap, vmin=vmin, vmax=vmax)
    cbar = plt.colorbar(im, ax=ax, fraction=0.046)
    cbar.ax.tick_params(labelsize=fontsize - 4)
    if title is not None:
        ax.set_title(title, fontsize=fontsize)


def plot_2d_pde(
    output: np.ndarray,
    data_all,
    times,
    input_len,
    plot_title,
    filename,
    folder="",
    use_wandb=False,
    epoch=0,
    dim = -1,
    input_step=0,
    output_step=-1,
):
    """
    output:     (output_len, x_num, x_num, data_dim)
    data_all:   (input_len + output_len, x_num, x_num, data_dim)
    times:      (input_len + output_len)
    """

    if output_step < 0:
        output_step = output.shape[0] + output_step

    if dim < 0:
        dim = output.shape[-1]
    input = data_all[:input_len]  # (input_len, x_num, x_num, data_dim)
    target = data_all[input_len:]  # (output_len, x_num, x_num, data_dim)

    input_times = times[:input_len]
    output_times = times[input_len:]

    fig, axs = plt.subplots(dim, 4, figsize=(5 * 4, 4.5 * dim))

    for j in range(dim):
        plot_ax(axs[j, 0], input[input_step, ..., j], f"input, step {input_step}, t={input_times[input_step]:.2f}")
        cur_target = target[output_step, ..., j]
        plot_ax(axs[j, 1], cur_target, f"target, step {input_len+output_step}, t={output_times[output_step]:.2f}")
        cur_output = output[output_step, ..., j]
        plot_ax(axs[j, 2], cur_output, f"output, step {input_len+output_step}, t={output_times[output_step]:.2f}")
        diff = cur_target - cur_output
        plot_ax(axs[j, 3], diff, "diff")

    for ax in axs.flat:
        ax.label_outer()
        ax.tick_params(axis="both", labelsize=11)

    plt.suptitle(plot_title + "\n", fontsize=20)
    plt.tight_layout()

    path = os.path.join(folder, filename + ".png")
    plt.savefig(path)
    plt.close(fig)
    return path


def plot_1d_pde(
    output_1: np.ndarray,
    output_2:None,
    time,
    coords,
    data_all,
    input_len,
    plot_title,
    filename,
    folder="",
    use_wandb=False,
    epoch=0,
    dim=-1,
    input_step=1,
    output_step=1,
    output_start=None,
    diff_plot = True,
    input_plot = True,
        input_start = 0,
        output_end = None
):
    """
    Plot 1D PDE data including input, target, output, and difference.
    If output_2 is None, only plots related to output_1 are generated.
    - output: (output_len//output_step, x_num, data_dim)
    - data_all: (input_len + output_len, x_num, data_dim)
    - time: (input_len + output_len)
    """
    if output_start is None:
        output_start = input_len + input_start
    if dim < 0:
        dim = output_1.shape[-1]
    if output_end is None or  output_end ==-1 :
        output_end = data_all.shape[0]
    # Ensure time and coords are numpy arrays
    time = np.array(time)
    coords = np.array(coords)

    # Slice data for input and target
    input = data_all[input_start:input_len+input_start:input_step]
    target = data_all[output_start:output_end:output_step]
    input_time = time[input_start:input_len+input_start:input_step]
    output_time = time[output_start:output_end:output_step]

    if input_plot:
        num_plots = 3
    else:
        num_plots = 2
    if diff_plot:
        num_plots += 1
    if output_2 is not None:
        num_plots += 2
    fig, axs = plt.subplots(dim, num_plots, figsize=(5 * num_plots, 4.5 * dim))
    if len(axs.shape) == 1:
        axs = axs.reshape(dim, num_plots)

    vmin = min(np.min(input), np.min(target), np.min(output_1))
    vmax = max(np.max(input), np.max(target), np.max(output_1))
    if output_2 is not None:
        vmin = min(vmin, np.min(output_2))
        vmax = max(vmax, np.max(output_2))
    for j in range(dim):
        if input_plot:
            # Create the data list considering if output_2 is provided
            data_list = [input[..., j], target[..., j], output_1[..., j]]
            titles = ['Input', 'Target', 'Output']
            uniform_color = [0,1,2]
        else:
            # Create the data list considering if output_2 is provided
            data_list = [target[..., j], output_1[..., j]]
            titles = [ 'Target', 'Output']
            uniform_color = [0,1]
        if diff_plot:
            data_list.extend([ target[..., j] - output_1[..., j]])
            titles.extend(['Diff'])
        if output_2 is not None:
            assert diff_plot
            uniform_color.append(len(titles))
            titles[2] = 'Output_zero_shot'
            titles[3] = 'Diff_zero_shot'
            data_list.extend([output_2[..., j], target[..., j] - output_2[..., j]])
            titles.extend(['Output_few_shot', 'Diff_few_shot'])


        for i, data in enumerate(data_list):
            num_x_ticks = 10
            num_y_ticks = 5
            if i in uniform_color:
                vminn,vmaxx = vmin,vmax
            else:
                vminn,vmaxx = None,None
            im = axs[j, i].imshow(data, aspect='auto',vmin=vminn, vmax =vmaxx)
            axs[j, i].set_title(titles[i])

            # Calculate tick positions and labels for x and y
            x_tick_positions = np.linspace(0, data.shape[1] - 1, num=num_x_ticks, dtype=int)
            y_tick_positions = np.linspace(0, data.shape[0] - 1, num=num_y_ticks, dtype=int)
            x_tick_labels = [f"{coords[idx]:.2f}" for idx in x_tick_positions]
            y_tick_labels = [f"{input_time[idx]:.2f}" if i == 0 else f"{output_time[idx]:.2f}" for idx in y_tick_positions]

            axs[j, i].set_xticks(x_tick_positions)
            axs[j, i].set_xticklabels(x_tick_labels)
            axs[j, i].set_yticks(y_tick_positions)
            axs[j, i].set_yticklabels(y_tick_labels)
            plt.colorbar(im, ax=axs[j, i])
    if plot_title is not None:
        plt.suptitle(plot_title, fontsize=20)
    plt.tight_layout()
    path = os.path.join(folder, filename + ".png")
    plt.savefig(path)
    plt.close(fig)
    return path
